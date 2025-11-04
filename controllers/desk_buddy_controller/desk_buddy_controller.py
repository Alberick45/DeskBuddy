import threading
import time
import requests
from controller import Robot, Keyboard
from flask import Flask, request, jsonify
from datetime import datetime, timedelta
import re

# Webots time step
TIME_STEP = 32

# ==========================================
# FLASK APP SETUP
# ==========================================
app = Flask(__name__)
robot_instance = None


@app.route("/command", methods=["POST"])
def handle_command():
    """Main endpoint to receive robot and task commands."""
    global robot_instance
    if not robot_instance:
        return jsonify({"error": "Robot not initialized"}), 503

    data = request.get_json(force=True)
    action = data.get("action")
    duration = float(data.get("duration", 2.0))
    message = data.get("message", "")
    reminder_text = data.get("reminder_text", "")

    print(f"[API] Received: {action}")

    # Robot movement & actions
    if action == "forward":
        robot_instance.run_async(lambda: robot_instance.move_forward(duration))
    elif action == "backward":
        robot_instance.run_async(lambda: robot_instance.move_backward(duration))
    elif action == "turn_left":
        robot_instance.run_async(lambda: robot_instance.turn("left", duration))
    elif action == "turn_right":
        robot_instance.run_async(lambda: robot_instance.turn("right", duration))
    elif action == "speak":
        robot_instance.run_async(lambda msg=message: robot_instance.speak(msg))
    elif action == "blink":
        robot_instance.run_async(robot_instance.blink_lights)
    elif action == "wave":
        robot_instance.run_async(robot_instance.wave)
    elif action == "patrol_mode":
        robot_instance.run_async(robot_instance.patrol_mode)
    elif action == "dance":
        robot_instance.run_async(robot_instance.dance)
    elif action == "turn_and_speak":
        robot_instance.run_async(lambda msg=message: robot_instance.turn_and_speak(msg))
    elif action == "all_actions":
        robot_instance.run_async(robot_instance.all_actions)
    elif action == "stop":
        robot_instance.stop_all()

    # Reminder/task commands
    elif action == "add_reminder":
        robot_instance.add_reminder_from_text(reminder_text)
        return jsonify({"status": "Reminder added"}), 200

    elif action == "list_tasks":
        tasks = robot_instance.get_tasks()
        return jsonify({"tasks": tasks}), 200

    elif action == "clear_tasks":
        robot_instance.clear_tasks()
        return jsonify({"status": "All tasks cleared"}), 200

    else:
        return jsonify({"error": f"Unknown action '{action}'"}), 400

    return jsonify({"status": f"Action '{action}' executed"}), 200


def start_api_server():
    """Run Flask API in a background thread."""
    print("🚀 Starting local control API on http://localhost:8000/command")
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False, threaded=True)


# ==========================================
# DESK BUDDY (Robot)
# ==========================================
class DeskBuddy(Robot):
    def __init__(self):
        super().__init__()

        # Threading & locks
        self.action_lock = threading.Lock()
        self.active_threads = []

        # Task management
        self.tasks = []
        self.api_url = "http://localhost:3000/api/tasks"

        # Key debouncing
        self.last_key_time = {}
        self.key_cooldown = 0.18
        self.key_timestamps = {}

        # Extra typing debounce
        self.typing_cooldown = 0.15

        # INPUT MODE STATE MACHINE
        self.input_mode = "idle"
        self.typed_text = ""

        # Devices
        self.led_left = self.getDevice("eye_led_left")
        self.led_right = self.getDevice("eye_led_right")

        self.speaker = self.getDevice("speaker")
        try:
            self.speaker.setLanguage("en-US")
        except Exception:
            pass

        self.head_motor = self.getDevice("tilt_motor")
        try:
            self.head_motor.setPosition(0.0)
        except Exception:
            pass

        # Arms
        self.left_hand_motor = self.getDevice("left_arm_motor")
        self.right_hand_motor = self.getDevice("right_arm_motor")
        try:
            self.left_hand_motor.setPosition(0.0)
            self.right_hand_motor.setPosition(0.0)
        except Exception:
            pass

        # Wheel motors
        self.left_wheel = self.getDevice("left_wheel_motor")
        self.right_wheel = self.getDevice("right_wheel_motor")
        self.left_rear_wheel = self.getDevice("left_rear_wheel_motor")
        self.right_rear_wheel = self.getDevice("right_rear_wheel_motor")
        for wheel in [self.left_wheel, self.right_wheel, self.left_rear_wheel, self.right_rear_wheel]:
            try:
                wheel.setPosition(float('inf'))
                wheel.setVelocity(0.0)
            except Exception:
                pass

        # Movement parameters
        self.max_speed = 6.28
        self.turn_speed = 3.0

    # -----------------------
    # NLP parsing for reminders
    # -----------------------
    def parse_reminder_nlp(self, text):
        """Advanced NLP parsing for date/time extraction."""
        now = datetime.now()

        reminder_date = now.strftime("%Y-%m-%d")
        reminder_time = "12:00"
        task_name = text.strip()

        text_lower = text.lower()

        # TIME extraction
        time_match = re.search(r'(\b\d{1,2}:\d{2}\b)\s*(am|pm)?', text_lower)
        if time_match:
            time_part = time_match.group(1)
            ampm = time_match.group(2)
            hour, minute = map(int, time_part.split(':'))
            if ampm:
                ampm = ampm.lower()
                if ampm == 'pm' and hour != 12:
                    hour += 12
                if ampm == 'am' and hour == 12:
                    hour = 0
            reminder_time = f"{hour:02d}:{minute:02d}"
            task_name = task_name.replace(time_match.group(0), '').strip()
        else:
            time_match2 = re.search(r'\b(\d{1,2})\s*(am|pm)\b', text_lower)
            if time_match2:
                hour = int(time_match2.group(1))
                ampm = time_match2.group(2).lower()
                if ampm == 'pm' and hour != 12:
                    hour += 12
                if ampm == 'am' and hour == 12:
                    hour = 0
                reminder_time = f"{hour:02d}:00"
                task_name = task_name.replace(time_match2.group(0), '').strip()

        # DATE extraction
        if 'tomorrow' in text_lower:
            reminder_date = (now + timedelta(days=1)).strftime("%Y-%m-%d")
            task_name = re.sub(r'\btomorrow\b', '', task_name, flags=re.IGNORECASE).strip()
        elif 'today' in text_lower:
            reminder_date = now.strftime("%Y-%m-%d")
            task_name = re.sub(r'\btoday\b', '', task_name, flags=re.IGNORECASE).strip()
        elif 'next week' in text_lower:
            reminder_date = (now + timedelta(days=7)).strftime("%Y-%m-%d")
            task_name = re.sub(r'next week', '', task_name, flags=re.IGNORECASE).strip()

        # Weekday names
        weekdays = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
            'friday': 4, 'saturday': 5, 'sunday': 6
        }

        for day_name, day_num in weekdays.items():
            if re.search(rf'\b(next\s+)?{day_name}\b', text_lower):
                current_weekday = now.weekday()
                days_ahead = (day_num - current_weekday) % 7
                if days_ahead == 0 and 'next ' not in text_lower:
                    days_ahead = 0
                if re.search(rf'\bnext\s+{day_name}\b', text_lower):
                    days_ahead = (day_num - current_weekday) % 7 + 7
                if days_ahead == 0 and 'next ' in text_lower:
                    days_ahead = 7
                reminder_date = (now + timedelta(days=days_ahead)).strftime("%Y-%m-%d")
                task_name = re.sub(rf'\b(next\s+)?{day_name}\b', '', task_name, flags=re.IGNORECASE).strip()
                break

        # Month name + day (multiple formats)
        month_names = {
            'jan': 1, 'january': 1, 'feb': 2, 'february': 2,
            'mar': 3, 'march': 3, 'apr': 4, 'april': 4,
            'may': 5, 'jun': 6, 'june': 6, 'jul': 7, 'july': 7,
            'aug': 8, 'august': 8, 'sep': 9, 'sept': 9, 'september': 9,
            'oct': 10, 'october': 10, 'nov': 11, 'november': 11,
            'dec': 12, 'december': 12
        }

        # Try: "nov 21", "november 21"
        for mname, mnum in month_names.items():
            match = re.search(rf'\b{mname}\s+(\d{{1,2}})\b', text_lower)
            if match:
                day = int(match.group(1))
                year = now.year
                try:
                    candidate = datetime(year, mnum, day)
                    if candidate < now:
                        candidate = datetime(year + 1, mnum, day)
                    reminder_date = candidate.strftime("%Y-%m-%d")
                    task_name = re.sub(rf'\b{mname}\s+\d{{1,2}}\b', '', task_name, flags=re.IGNORECASE).strip()
                except ValueError:
                    pass
                break

        # Try: "21 nov", "21 november", "21st november"
        for mname, mnum in month_names.items():
            match = re.search(rf'\b(\d{{1,2}})(?:st|nd|rd|th)?\s+{mname}\b', text_lower)
            if match:
                day = int(match.group(1))
                year = now.year
                try:
                    candidate = datetime(year, mnum, day)
                    if candidate < now:
                        candidate = datetime(year + 1, mnum, day)
                    reminder_date = candidate.strftime("%Y-%m-%d")
                    task_name = re.sub(rf'\b\d{{1,2}}(?:st|nd|rd|th)?\s+{mname}\b', '', task_name, flags=re.IGNORECASE).strip()
                except ValueError:
                    pass
                break

        # Try: numeric formats "21/11", "21/10", "11/21" (DD/MM or MM/DD)
        numeric_date = re.search(r'\b(\d{1,2})[/\-](\d{1,2})\b', text_lower)
        if numeric_date and reminder_date == now.strftime("%Y-%m-%d"):
            part1 = int(numeric_date.group(1))
            part2 = int(numeric_date.group(2))
            year = now.year
            
            # Try DD/MM first (European format)
            try:
                if part1 <= 31 and part2 <= 12:
                    candidate = datetime(year, part2, part1)
                    if candidate < now:
                        candidate = datetime(year + 1, part2, part1)
                    reminder_date = candidate.strftime("%Y-%m-%d")
                    task_name = re.sub(r'\b\d{1,2}[/\-]\d{1,2}\b', '', task_name).strip()
            except ValueError:
                # Try MM/DD (US format)
                try:
                    if part1 <= 12 and part2 <= 31:
                        candidate = datetime(year, part1, part2)
                        if candidate < now:
                            candidate = datetime(year + 1, part1, part2)
                        reminder_date = candidate.strftime("%Y-%m-%d")
                        task_name = re.sub(r'\b\d{1,2}[/\-]\d{1,2}\b', '', task_name).strip()
                except ValueError:
                    pass

        # Final cleanup
        task_name = re.sub(r'\s+', ' ', task_name)
        task_name = re.sub(r'\b(remind me|reminder|on|at)\b', '', task_name, flags=re.IGNORECASE).strip()
        task_name = task_name.lstrip(',:;-').strip()
        if not task_name:
            task_name = "Reminder"

        return task_name, reminder_date, reminder_time

    # -----------------------
    # Key debouncing helpers
    # -----------------------
    def is_key_ready(self, key, cooldown=0.2):
        """Check if enough time has passed since last key press."""
        now = time.time()
        last_time = self.key_timestamps.get(key, 0)
        diff = now - last_time

        if diff >= cooldown:
            self.key_timestamps[key] = now
            return True
        else:
            return False

    # -----------------------
    # Tasks / reminders
    # -----------------------
    def add_reminder_from_text(self, text):
        if not text or not text.strip():
            print("⚠️ No reminder text provided.")
            return

        task_name, reminder_date, reminder_time = self.parse_reminder_nlp(text)
        # 🧹 Clean up the extracted text before storing
        if task_name:
            task_name = task_name.strip()
            if task_name.isupper():
                task_name = task_name.lower().capitalize()
        task = {
            "name": task_name,
            "date": reminder_date,
            "time": reminder_time,
            "created": datetime.now().isoformat(),
            "type": "reminder"
        }

        with self.action_lock:
            self.tasks.append(task)

        print(f"✅ Reminder added: {task_name} — {reminder_date} {reminder_time}")
        # Only speak AFTER reminder is fully processed
        spoken_text = f"Reminder set: {task_name}, on {reminder_date} at {reminder_time}"
        self.run_async(lambda: self.speak(spoken_text))

        def sync_add():
            try:
                response = requests.post(self.api_url, json=task, timeout=5)
                if response.status_code in (200, 201):
                    print("🌐 Synced to API")
                else:
                    print(f"⚠️ Sync failed ({response.status_code})")
            except Exception as e:
                print(f"🚫 Could not reach API: {e}")

        threading.Thread(target=sync_add, daemon=True).start()

    def get_tasks(self):
        """Get tasks from API with safe fallback to local list."""
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                fetched = response.json()
                with self.action_lock:
                    self.tasks = fetched
                print(f"🌐 Fetched {len(fetched)} tasks from API")
                return fetched
        except requests.exceptions.RequestException as e:
            print(f"🚫 Using local tasks: {e}")

        with self.action_lock:
            return list(self.tasks)

    def list_tasks_vocal(self):
        """List tasks, sort by closeness to now, and speak top items."""
        from datetime import datetime as dt

        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                server_tasks = response.json()
                with self.action_lock:
                    self.tasks = server_tasks
                print("🌐 Fetched tasks from API")
        except requests.exceptions.RequestException as e:
            print(f"🚫 Using local tasks: {e}")

        with self.action_lock:
            task_list = list(self.tasks)

        if not task_list:
            print("📋 No tasks available.")
            self.speak("You have no tasks.")
            return

        def parse_task_datetime(task):
            try:
                date_str = task.get('date', '')
                time_str = task.get('time', '00:00')
                dt_str = f"{date_str} {time_str}"
                return dt.strptime(dt_str, "%Y-%m-%d %H:%M")
            except Exception:
                return dt.max

        now = dt.now()
        sorted_tasks = sorted(task_list, key=lambda t: abs((parse_task_datetime(t) - now).total_seconds()))
        print(f"\n📋 YOU HAVE {len(sorted_tasks)} TASKS:")
        for i, t in enumerate(sorted_tasks, 1):
            td = parse_task_datetime(t)
            if td != dt.max:
                is_past = td < now
                date_display = "Today" if td.date() == now.date() else t.get('date', 'No date')
                status = "⏰ PAST" if is_past else "🔜 UPCOMING"
            else:
                date_display = t.get('date', 'No date')
                status = "❓ NO DATE"
            print(f"{i}. {t.get('name')} - {date_display} at {t.get('time')} {status}")

        total = len(sorted_tasks)
        self.speak(f"You have {total} tasks.")
        upcoming = [t for t in sorted_tasks if parse_task_datetime(t) >= now][:3]
        if upcoming:
            self.speak("Your next tasks are:")
            for t in upcoming:
                self.speak(f"{t.get('name')}, on {t.get('date')} at {t.get('time')}")

    def clear_tasks(self):
        with self.action_lock:
            count = len(self.tasks)
            if count == 0:
                print("📋 No tasks to clear.")
                self.speak("No tasks to clear.")
                return
            self.tasks.clear()
        print(f"🧹 Cleared {count} tasks.")
        self.speak(f"Cleared {count} tasks.")
        try:
            response = requests.delete(self.api_url, timeout=5)
            if response.status_code in (200, 204):
                print("🌐 Cleared all from API")
        except Exception as e:
            print(f"🚫 API clear failed: {e}")

    # -----------------------
    # Movement helpers
    # -----------------------
    def move_forward(self, duration=None):
        if duration:
            self.set_wheel_velocity(2.0)
            time.sleep(duration)
            self.stop()
        else:
            self.set_wheel_velocity(self.max_speed)

    def move_backward(self, duration=None):
        if duration:
            self.set_wheel_velocity(-2.0)
            time.sleep(duration)
            self.stop()
        else:
            self.set_wheel_velocity(-self.max_speed)

    def turn(self, direction, duration):
        if direction.lower() == 'left':
            self.set_wheel_velocity_differential(-self.turn_speed, self.turn_speed)
        elif direction.lower() == 'right':
            self.set_wheel_velocity_differential(self.turn_speed, -self.turn_speed)
        time.sleep(duration)
        self.stop()

    def set_wheel_velocity(self, velocity):
        with self.action_lock:
            try:
                self.left_wheel.setVelocity(velocity)
                self.right_wheel.setVelocity(velocity)
                self.left_rear_wheel.setVelocity(velocity)
                self.right_rear_wheel.setVelocity(velocity)
            except Exception:
                pass

    def set_wheel_velocity_differential(self, left_vel, right_vel):
        with self.action_lock:
            try:
                self.left_wheel.setVelocity(left_vel)
                self.right_wheel.setVelocity(right_vel)
                self.left_rear_wheel.setVelocity(left_vel)
                self.right_rear_wheel.setVelocity(right_vel)
            except Exception:
                pass

    def stop(self):
        with self.action_lock:
            try:
                self.left_wheel.setVelocity(0.0)
                self.right_wheel.setVelocity(0.0)
                self.left_rear_wheel.setVelocity(0.0)
                self.right_rear_wheel.setVelocity(0.0)
            except Exception:
                pass

    # -----------------------
    # Actions
    # -----------------------
    def speak(self, message):
        """Speak with LED animation."""
        print(f"🗣️ Speaking: '{message}'")
        try:
            self.speaker.speak(message, 1.0)
        except Exception:
            pass

        words = len(message.split())
        speak_duration = max(1.0, words * 0.28)
        blink_interval = 0.45
        elapsed = 0.0
        while elapsed < speak_duration:
            with self.action_lock:
                try:
                    self.led_left.set(1)
                    self.led_right.set(1)
                except Exception:
                    pass
            sleep_time = max(0, min(blink_interval / 2, speak_duration - elapsed))
            if sleep_time > 0:
                time.sleep(sleep_time)
            elapsed += blink_interval / 2
            
            with self.action_lock:
                try:
                    self.led_left.set(0)
                    self.led_right.set(0)
                except Exception:
                    pass
            sleep_time = max(0, min(blink_interval / 2, speak_duration - elapsed))
            if sleep_time > 0:
                time.sleep(sleep_time)
            elapsed += blink_interval / 2

    def wave(self):
        print("👋 Waving...")
        with self.action_lock:
            try:
                self.head_motor.setPosition(0.2)
                self.right_hand_motor.setPosition(1)
            except Exception:
                pass
        time.sleep(0.5)
        with self.action_lock:
            try:
                self.head_motor.setPosition(-0.2)
                self.right_hand_motor.setPosition(-1)
            except Exception:
                pass
        time.sleep(0.5)
        with self.action_lock:
            try:
                self.head_motor.setPosition(0.0)
                self.right_hand_motor.setPosition(0.0)
            except Exception:
                pass

    def blink_lights(self):
        print("✨ Blinking lights...")
        for _ in range(3):
            with self.action_lock:
                try:
                    self.led_left.set(1)
                    self.led_right.set(1)
                except Exception:
                    pass
            time.sleep(0.25)
            with self.action_lock:
                try:
                    self.led_left.set(0)
                    self.led_right.set(0)
                except Exception:
                    pass
            time.sleep(0.25)

    def say_hello(self):
        self.speak("Hello! I'm your Robo Desk Buddy!")

    def patrol_mode(self):
        """Simple patrol: move forward, turn, repeat."""
        print("🚶 Starting patrol mode...")
        for _ in range(4):
            self.move_forward(2)
            self.turn("right", 1)
        self.stop()
        print("🚶 Patrol mode ended.")
    
    def dance(self):
        """Simple dance routine."""
        print("💃 Starting dance...")
        for _ in range(2):
            self.turn("left", 0.5)
            self.turn("right", 0.5)
        self.wave()
        self.blink_lights()
        print("💃 Dance ended.")
    
    def turn_and_speak(self, message):
        """Turn left while speaking a message."""
        print("🔄 Turning and speaking...")
        self.run_async(lambda: self.turn("left", 3))
        self.speak(message)
        print("🔄 Turn and speak ended.")
    
    def all_actions(self):
        """Perform all actions simultaneously."""
        print("🤹 Performing all actions...")
        self.run_async(lambda: self.move_forward(5))
        self.run_async(self.wave)
        self.run_async(self.blink_lights)
        self.run_async(lambda: self.speak("I am dancing while moving!"))
        print("🤹 All actions started.")

    # -----------------------
    # Async thread runner
    # -----------------------
    def run_async(self, func):
        def wrapper():
            try:
                func()
            except Exception as e:
                print(f"❌ Thread error: {e}")
            finally:
                with self.action_lock:
                    thr = threading.current_thread()
                    if thr in self.active_threads:
                        self.active_threads.remove(thr)

        thread = threading.Thread(target=wrapper, daemon=True)
        with self.action_lock:
            self.active_threads.append(thread)
        thread.start()
        return thread

    def stop_all(self):
        print("🛑 Stopping all...")
        with self.action_lock:
            try:
                self.head_motor.setPosition(0.0)
                self.led_left.set(0)
                self.led_right.set(0)
            except Exception:
                pass
            self.set_wheel_velocity(0.0)

    # -----------------------
    # Input handling (typing)
    # -----------------------
    def handle_debug_typing(self, key):
        """DEBUG MODE: IMMEDIATE PRINT - Test typing and find special key codes."""
        
        # PRINT EVERY KEY IMMEDIATELY - NO CONDITIONS
        print(f"[KEY={key}]", end="", flush=True)
        
        # Exit on TAB
        if key == 1:
            self.input_mode = "idle"
            self.typed_text = ""
            print("\n✅ DEBUG MODE ENDED\n")
            return
        
        # If printable, also show the character
        if 32 <= key <= 126:
            ch = chr(key)
            self.typed_text += ch
            print(f"'{ch}' ", end="", flush=True)
        
        # Show text after ENTER
        if key == 4:
            print(f"\n📝 Full text: '{self.typed_text}'\n")
            print("Debug: ", end="", flush=True)
    
    def handle_reminder_input(self, key):
        """Handle typing for reminder mode with proper key debouncing."""
        
        # Webots special keys (confirmed non-standard)
        WEBOTS_BACKSPACE = 3
        WEBOTS_ENTER = 4
        WEBOTS_ESC = 1  # TAB key = 1 in Webots
        
        # ENTER key (Webots uses key 4)
        if key == WEBOTS_ENTER:
            if not self.is_key_ready('ENTER', cooldown=0.3):
                return  # Debounce
            reminder_text = self.typed_text.strip()
            if reminder_text:
                print(f"\n\n🔍 Processing: '{reminder_text}'")
                self.add_reminder_from_text(reminder_text)
                self.input_mode = "idle"
                self.typed_text = ""
                print("\n✅ Reminder created! Back to normal mode.\n")
            else:
                print("\n⚠️ Cannot create empty reminder.")
            return

        # BACKSPACE key (Webots uses key 3)
        if key == WEBOTS_BACKSPACE:
            if not self.is_key_ready('BACKSPACE', cooldown=0.2):
                return  # Debounce
            if self.typed_text:
                self.typed_text = self.typed_text[:-1]
                # Clear entire line and reprint with label
                print(f"\r{' ' * 100}\rReminder: {self.typed_text}", end="", flush=True)
            return

        # ESCAPE key (TAB = key 1 in Webots)
        if key == WEBOTS_ESC:
            if not self.is_key_ready('ESC', cooldown=0.3):
                return  # Debounce
            self.input_mode = "idle"
            self.typed_text = ""
            print(f"\n\n❌ Reminder entry canceled. Back to normal mode.\n")
            return

        # Printable characters (ASCII 32–126)
        # Print character immediately, one at a time
        if 32 <= key <= 126:
            # Check cooldown to prevent repeats
            if not self.is_key_ready(key, cooldown=0.12):
                return  # Debounce - ignore this keypress
            
            try:
                ch = chr(key)
                self.typed_text += ch
                # Print just the new character immediately
                print(ch, end="", flush=True)
            except Exception as e:
                print(f"\n[ERROR] Failed to add character: {e}")


# ==========================================
# MAIN
# ==========================================
def main():
    global robot_instance
    bot = DeskBuddy()
    robot_instance = bot

    keyboard = bot.getKeyboard()
    keyboard.enable(TIME_STEP)

    # Start Flask API thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    # User guidance
    print("=" * 70)
    print("🤖 DESKBUDDY ROBOT - REMINDER SYSTEM")
    print("=" * 70)
    print("MOVEMENT:  F=Forward | R=Backward | L=Turn Left | G=Turn Right | Space=Stop")
    print("THREADED:  P=Patrol | D=Dance | Y=All Actions | T=Turn & Speak")
    print("ACTIONS:   W=Wave | B=Blink | H=Say Hello")
    print("REMINDERS: M=Add Reminder (NLP) | K=List Tasks | C=Clear All")
    print("DEBUG:     X=Test Typing Mode (find key codes)")
    print("SYSTEM:    S=Stop All | Q=Quit")
    print("=" * 70)
    print("📡 API: http://localhost:8000/command")
    print("=" * 70)
    print("\nExamples:")
    print("  'remind me at 5 pm tomorrow'")
    print("  'team meeting on thursday aug 18 at 2 pm'")
    print("  'call mom today at 3:30 pm'")
    print("=" * 70)

    while bot.step(TIME_STEP) != -1:
        key = keyboard.getKey()
        if key == -1:
            continue

        # If in debug typing mode
        if bot.input_mode == "debug_typing":
            bot.handle_debug_typing(key)
            continue

        # If typing in reminder mode
        if bot.input_mode == "adding_reminder":
            bot.handle_reminder_input(key)
            continue

        # Idle mode controls
        if key == ord('F'):
            if bot.is_key_ready('F'):
                bot.move_forward()
        elif key == ord('R'):
            if bot.is_key_ready('R'):
                bot.move_backward()
        elif key == ord('L'):
            if bot.is_key_ready('L'):
                bot.set_wheel_velocity_differential(-bot.turn_speed, bot.turn_speed)
        elif key == ord('G'):
            if bot.is_key_ready('G'):
                bot.set_wheel_velocity_differential(bot.turn_speed, -bot.turn_speed)
        elif key == ord(' '):
            if bot.is_key_ready('SPACE'):
                bot.stop()

        # Threaded Movement
        elif key == ord('P'):
            if bot.is_key_ready('P'):
                bot.run_async(bot.patrol_mode)
        elif key == ord('D'):
            if bot.is_key_ready('D'):
                bot.run_async(bot.dance)
        elif key == ord('Y'):
            if bot.is_key_ready('Y'):
                bot.run_async(bot.all_actions)
        elif key == ord('T'):
            if bot.is_key_ready('T'):
                bot.run_async(lambda: bot.turn_and_speak("I am turning left while speaking!"))

        # Actions
        elif key == ord('W'):
            if bot.is_key_ready('W'):
                bot.run_async(bot.wave)
        elif key == ord('B'):
            if bot.is_key_ready('B'):
                bot.run_async(bot.blink_lights)
        elif key == ord('H'):
            if bot.is_key_ready('H'):
                bot.run_async(bot.say_hello)

        # Debug Mode
        elif key == ord('X'):
            if bot.is_key_ready('X'):
                bot.input_mode = "debug_typing"
                bot.typed_text = ""
                # Clear X from timestamps
                bot.key_timestamps.clear()
                print("\n" + "=" * 60)
                print("🐛 DEBUG TYPING MODE")
                print("=" * 60)
                print("Type anything. Special keys will show their codes.")
                print("Press TAB to exit debug mode.")
                print("=" * 60 + "\n")
                print("Debug: ", end="", flush=True)

        # Reminders
        elif key == ord('M'):
            if bot.is_key_ready('M'):
                bot.input_mode = "adding_reminder"
                bot.typed_text = ""  # Clear any previous text
                # Clear the 'M' key timestamp so it doesn't get registered as typed text
                if 'M' in bot.key_timestamps:
                    del bot.key_timestamps['M']
                if ord('M') in bot.key_timestamps:
                    del bot.key_timestamps[ord('M')]
                print("\n" + "=" * 60)
                print("⏰ ADD REMINDER MODE - NATURAL LANGUAGE")
                print("=" * 60)
                print("Type your reminder and press ENTER (Webots ENTER=4)")
                print("Press TAB to cancel")
                print("=" * 60)
                print("Examples: 'nov 21', '21st november', '21/11', 'tomorrow at 5pm'")
                print("=" * 60 + "\n")
                # NO SPEECH - just show the prompt immediately
                print("Reminder: ", end="", flush=True)

        elif key == ord('K'):
            if bot.is_key_ready('K'):
                bot.run_async(bot.list_tasks_vocal)

        elif key == ord('C'):
            if bot.is_key_ready('C'):
                bot.run_async(bot.clear_tasks)

        # System
        elif key == ord('S'):
            if bot.is_key_ready('S'):
                bot.stop_all()
        elif key == ord('Q'):
            if bot.is_key_ready('Q'):
                print("👋 Quitting...")
                bot.stop_all()
                break

    print("🤖 Desk Buddy shutting down...")


if __name__ == "__main__":
    main()