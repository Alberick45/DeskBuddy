import threading
import time
import requests
from controller import Robot, Keyboard
from flask import Flask, request, jsonify
from datetime import datetime

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
    
    # Task-specific fields
    task_name = data.get("task_name", "")
    task_date = data.get("date", "")
    task_time = data.get("time", "")
    
    print(f"[API] Received: {action}")

    # ====== ROBOT MOVEMENT & ACTIONS ======
    if action == "forward":
        robot_instance.run_async(lambda: robot_instance.move_forward(duration))
    elif action == "backward":
        robot_instance.run_async(lambda: robot_instance.move_backward(duration))
    elif action == "turn_left":
        robot_instance.run_async(lambda: robot_instance.turn("left", duration))
    elif action == "turn_right":
        robot_instance.run_async(lambda: robot_instance.turn("right", duration))
    elif action == "speak":
        robot_instance.run_async(lambda: robot_instance.speak(message))
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

    # ====== TASK COMMANDS ======
    elif action == "add_task":
        task = {
            "name": task_name,
            "date": task_date,
            "time": task_time,
            "created": datetime.now().isoformat()
        }
        robot_instance.add_task(task)
        return jsonify({"status": "Task added", "task": task}), 200
        
    elif action == "list_tasks":
        tasks = robot_instance.get_tasks()
        return jsonify({"tasks": tasks}), 200
        
    elif action == "remove_task":
        index = int(data.get("index", -1))
        removed = robot_instance.remove_task(index)
        return jsonify({"removed": removed}), 200
        
    elif action == "clear_tasks":
        robot_instance.clear_tasks()
        return jsonify({"status": "All tasks cleared"}), 200

    else:
        return jsonify({"error": f"Unknown action '{action}'"}), 400

    return jsonify({"status": f"Action '{action}' executed"}), 200


def start_api_server():
    """Run Flask API in a background thread."""
    print("🚀 Starting local control API on http://localhost:8000/command")
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)


class DeskBuddy(Robot):
    def __init__(self):
        super().__init__()
        
        # Threading control
        self.action_lock = threading.Lock()
        self.active_threads = []
        
        # Task management
        self.tasks = []
        self.api_url = "http://localhost:3000/api/tasks"

        # Get devices from world file
        self.led_left = self.getDevice("eye_led_left")
        self.led_right = self.getDevice("eye_led_right")
        self.speaker = self.getDevice("speaker")
        self.speaker.setLanguage("en-US")
        self.head_motor = self.getDevice("tilt_motor")
        self.head_motor.setPosition(0.0)

        # Arms 
        self.left_hand_motor = self.getDevice("left_arm_motor")
        self.left_hand_motor.setPosition(0.0)
        self.right_hand_motor = self.getDevice("right_arm_motor")
        self.right_hand_motor.setPosition(0.0)
        
        # Wheel motors
        self.left_wheel = self.getDevice("left_wheel_motor")
        self.right_wheel = self.getDevice("right_wheel_motor")
        self.left_rear_wheel = self.getDevice("left_rear_wheel_motor")
        self.right_rear_wheel = self.getDevice("right_rear_wheel_motor")
        
        for wheel in [self.left_wheel, self.right_wheel, self.left_rear_wheel, self.right_rear_wheel]:
            wheel.setPosition(float('inf'))
            wheel.setVelocity(0.0)
        
        # Movement parameters
        self.max_speed = 6.28
        self.turn_speed = 3.0

    # ========================
    # TASK MANAGEMENT
    # ========================
    def add_task(self, task):
        """Add a task with name, date, and time."""
        if not task or not task.get("name"):
            print("⚠️ No task name provided.")
            self.speak("Error: No task name provided.")
            return

        with self.action_lock:
            self.tasks.append(task)
            task_info = f"{task['name']} on {task.get('date', 'no date')} at {task.get('time', 'no time')}"
        
        # Speak OUTSIDE the lock
        print(f"✅ Task added: {task_info}")
        self.speak(f"Task added: {task['name']}")
        # Sync to external API (Next.js)
        try:
            response = requests.post(
                self.api_url,  # http://localhost:3000/api/tasks
                json=task,
                timeout=5
            )
            if response.status_code in [200, 201]:
                print(f"🌐 Synced to Next.js API successfully")
            else:
                print(f"⚠️ API sync failed (status {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"🚫 Could not reach Next.js API: {e}")
            print("   Task saved locally only")

    def get_tasks(self):
        """Get all tasks from external API (fallback to local)."""
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                fetched_tasks = response.json()
                
                # Update local cache
                with self.action_lock:
                    self.tasks = fetched_tasks
                
                print(f"🌐 Fetched {len(fetched_tasks)} tasks from Next.js API")
                return fetched_tasks
        except requests.exceptions.RequestException as e:
            print(f"🚫 Could not reach Next.js API: {e}")
            print("   Using local tasks")
        
        # Fallback to local
        with self.action_lock:
            return list(self.tasks)

    def list_tasks_vocal(self):
        """Fetch tasks from API, then list vocally (next 3 closest) and show all in console."""
        from datetime import datetime
        
        # Fetch from server first
        try:
            response = requests.get(self.api_url, timeout=5)
            if response.status_code == 200:
                server_tasks = response.json()
                # Update local list with server data
                with self.action_lock:
                    self.tasks = server_tasks
                print("🌐 Fetched tasks from Next.js API")
        except requests.exceptions.RequestException as e:
            print(f"🚫 Using local tasks only: {e}")
        
        # Now list them
        with self.action_lock:
            if not self.tasks:
                task_list = []
            else:
                task_list = list(self.tasks)
        
        if not task_list:
            print("📋 No tasks available.")
            self.speak("You have no tasks.")
            return
        
        # Sort tasks by date and time (closest first)
        def parse_task_datetime(task):
            """Parse task date/time into datetime object for sorting."""
            try:
                date_str = task.get('date', '')
                time_str = task.get('time', '00:00')
                
                # Try to parse the date (support multiple formats)
                datetime_str = f"{date_str} {time_str}"
                
                # Try ISO format first (YYYY-MM-DD)
                try:
                    return datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                except ValueError:
                    pass
                
                # Try other common formats
                for fmt in ["%B %d %Y %H:%M", "%m/%d/%Y %H:%M", "%d/%m/%Y %H:%M"]:
                    try:
                        return datetime.strptime(datetime_str, fmt)
                    except ValueError:
                        continue
                
                # If all parsing fails, return far future so it goes to end
                return datetime.max
            except Exception:
                return datetime.max
        
        # Get current time
        now = datetime.now()
        
        # Sort tasks: upcoming tasks first, then past tasks
        sorted_tasks = sorted(task_list, key=lambda t: abs((parse_task_datetime(t) - now).total_seconds()))
        
        # Print ALL tasks to console
        print(f"\n📋 YOU HAVE {len(sorted_tasks)} TASKS:")
        print("-" * 60)
        for i, task in enumerate(sorted_tasks, start=1):
            task_datetime = parse_task_datetime(task)
            if task_datetime != datetime.max:
                is_past = task_datetime < now
                status = "⏰ PAST" if is_past else "🔜 UPCOMING"
            else:
                status = "❓ NO DATE"
            
            task_str = f"{i}. {task.get('name', 'Unnamed')} - {task.get('date', 'No date')} at {task.get('time', 'No time')} {status}"
            print(task_str)
        print("-" * 60)
        
        # Get next 3 closest tasks (upcoming only, or all if less than 3)
        upcoming_tasks = [t for t in sorted_tasks if parse_task_datetime(t) >= now]
        
        # If no upcoming tasks, use the 3 most recent past tasks
        if not upcoming_tasks:
            closest_3 = sorted_tasks[:3]
            time_context = "most recent"
        else:
            closest_3 = upcoming_tasks[:3]
            time_context = "upcoming"
        
        # Speak summary + next 3 tasks
        total_count = len(sorted_tasks)
        self.speak(f"You have {total_count} task{'s' if total_count != 1 else ''}.")
        
        if closest_3:
            self.speak(f"Your {time_context} tasks are:")
            for task in closest_3:
                task_name = task.get('name', 'Unnamed task')
                task_date = task.get('date', 'no date')
                task_time = task.get('time', 'no time')
                self.speak(f"{task_name}, on {task_date} at {task_time}.")
        else:
            self.speak("No upcoming tasks.")

    def remove_task(self, index):
        """Remove a task by index locally AND from API."""
        with self.action_lock:
            if 0 <= index < len(self.tasks):
                removed = self.tasks.pop(index)
                task_id = removed.get('id')  # Assuming tasks have IDs
            else:
                print("⚠️ Invalid index for removal.")
                self.speak("Invalid task number.")
                return None
        
        print(f"🗑️ Removed locally: {removed.get('name', 'Unnamed')}")
        self.speak(f"Removed task: {removed.get('name', 'Task')}")
        
        # Sync deletion to API (if your API supports DELETE)
        if task_id:
            try:
                response = requests.delete(
                    f"{self.api_url}/{task_id}",
                    timeout=5
                )
                if response.status_code in [200, 204]:
                    print(f"🌐 Deleted from Next.js API")
                else:
                    print(f"⚠️ API delete failed (status {response.status_code})")
            except requests.exceptions.RequestException as e:
                print(f"🚫 Could not reach Next.js API: {e}")
        
        return removed

    def clear_tasks(self):
        """Clear all tasks locally AND on API."""
        with self.action_lock:
            count = len(self.tasks)
            if count == 0:
                print("📋 No tasks to clear.")
                return
            self.tasks.clear()
        
        print(f"🧹 Cleared {count} task{'s' if count != 1 else ''} locally.")
        self.speak(f"Cleared {count} task{'s' if count != 1 else ''}.")
        
        # Sync clear to API (if supported)
        try:
            response = requests.delete(self.api_url, timeout=5)
            if response.status_code in [200, 204]:
                print(f"🌐 Cleared all tasks from Next.js API")
            else:
                print(f"⚠️ API clear failed (status {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"🚫 Could not reach Next.js API: {e}")

    # ==========================================
    # MOVEMENT CONTROL
    # ==========================================
    def move_forward(self, duration=None):
        """Move forward (continuous if no duration, timed if duration given)."""
        if duration:
            print(f"Moving forward for {duration} seconds...")
            self.set_wheel_velocity(2.0)
            time.sleep(duration)
            self.stop()
        else:
            self.set_wheel_velocity(self.max_speed)

    def move_backward(self, duration=None):
        """Move backward."""
        if duration:
            print(f"Moving backward for {duration} seconds...")
            self.set_wheel_velocity(-2.0)
            time.sleep(duration)
            self.stop()
        else:
            self.set_wheel_velocity(-self.max_speed)

    def turn(self, direction, duration):
        """Turn left or right for specified duration."""
        print(f"Turning {direction} for {duration} seconds...")
        
        if direction.lower() == 'left':
            self.set_wheel_velocity_differential(-self.turn_speed, self.turn_speed)
        elif direction.lower() == 'right':
            self.set_wheel_velocity_differential(self.turn_speed, -self.turn_speed)
        
        time.sleep(duration)
        self.stop()

    def set_wheel_velocity(self, velocity):
        """Set all wheels to same velocity."""
        with self.action_lock:
            self.left_wheel.setVelocity(velocity)
            self.right_wheel.setVelocity(velocity)
            self.left_rear_wheel.setVelocity(velocity)
            self.right_rear_wheel.setVelocity(velocity)

    def set_wheel_velocity_differential(self, left_vel, right_vel):
        """Set left and right wheels to different velocities (for turning)."""
        with self.action_lock:
            self.left_wheel.setVelocity(left_vel)
            self.right_wheel.setVelocity(right_vel)
            self.left_rear_wheel.setVelocity(left_vel)
            self.right_rear_wheel.setVelocity(right_vel)

    def stop(self):
        """Stop all wheel movement."""
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)

    # ==========================================
    # ACTIONS
    # ==========================================
    def speak(self, message):
        """Speak message with LED animation."""
        print(f"🗣️ Speaking: '{message}'")
        
        try:
            self.speaker.speak(message, 1.0)
        except Exception as e:
            print(f"⚠️ Speaker error: {e}")
        
        # LED blinking during speech
        words = len(message.split())
        speak_duration = max(1.0, words * 0.3)
        blink_interval = 0.5
        elapsed_time = 0.0

        while elapsed_time < speak_duration:
            with self.action_lock:
                self.led_left.set(1)
                self.led_right.set(1)
            time.sleep(min(blink_interval/2, speak_duration - elapsed_time))
            elapsed_time += blink_interval/2

            if elapsed_time >= speak_duration:
                break

            with self.action_lock:
                self.led_left.set(0)
                self.led_right.set(0)
            time.sleep(min(blink_interval/2, speak_duration - elapsed_time))
            elapsed_time += blink_interval/2

        with self.action_lock:
            self.led_left.set(0)
            self.led_right.set(0)

    def wave(self):
        """Wave with head and right arm."""
        print("👋 Waving...")
        
        with self.action_lock:
            self.head_motor.setPosition(0.2)
            self.right_hand_motor.setPosition(1)
        time.sleep(0.5)
        
        with self.action_lock:
            self.head_motor.setPosition(-0.2)
            self.right_hand_motor.setPosition(-1)
        time.sleep(0.5)
        
        with self.action_lock:
            self.head_motor.setPosition(0.0)
            self.right_hand_motor.setPosition(0.0)

    def blink_lights(self):
        """Blink LEDs 3 times."""
        print("✨ Blinking...")
        for i in range(3):
            with self.action_lock:
                self.led_left.set(1)
                self.led_right.set(1)
            time.sleep(0.3)
            with self.action_lock:
                self.led_left.set(0)
                self.led_right.set(0)
            time.sleep(0.3)

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

    # ==========================================
    # THREADING
    # ==========================================
    def run_async(self, func):
        """Execute function in separate thread."""
        def wrapper():
            try:
                func()
            except Exception as e:
                print(f"❌ Thread error: {e}")
            finally:
                with self.action_lock:
                    if threading.current_thread() in self.active_threads:
                        self.active_threads.remove(threading.current_thread())
        
        thread = threading.Thread(target=wrapper, daemon=True)
        with self.action_lock:
            self.active_threads.append(thread)
        thread.start()
        return thread

    def stop_all(self):
        """Emergency stop - reset all devices."""
        print("🛑 Stopping all actions...")
        
        with self.action_lock:
            self.head_motor.setPosition(0.0)
            self.led_left.set(0)
            self.led_right.set(0)
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)


def main():
    global robot_instance
    bot = DeskBuddy()
    robot_instance = bot

    keyboard = bot.getKeyboard()
    keyboard.enable(TIME_STEP)

    # Start Flask API
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    print("=" * 70)
    print("🤖 DESKBUDDY ROBOT CONTROLS")
    print("=" * 70)
    print("MOVEMENT:  F=Forward | R=Backward | L=Turn Left | G=Turn Right | Space=Stop")
    print("Threading MOVEMENT:  P=Patrol Mode | D=Dance | Y=All Actions Simultaneously | T=Turn Left & Speak")
    print("ACTIONS:   W=Wave | B=Blink | H=Say Hello")
    print("TASKS:     A=Add Task Info | K=List Tasks | C=Clear Tasks")
    print("SYSTEM:    S=Stop All | Q=Quit")
    print("=" * 70)
    print("📡 API: http://localhost:8000/command")
    print("=" * 70)

    while bot.step(TIME_STEP) != -1:
        key = keyboard.getKey()
        
        # Movement
        if key == ord('F'):
            bot.move_forward()
        elif key == ord('R'):
            bot.move_backward()
        elif key == ord('L'):
            bot.set_wheel_velocity_differential(-bot.turn_speed, bot.turn_speed)
        elif key == ord('G'):
            bot.set_wheel_velocity_differential(bot.turn_speed, -bot.turn_speed)
        elif key == ord(' '):
            bot.stop()

        # Threaded Movement
        elif key == ord('P'):
            bot.run_async(bot.patrol_mode)

        elif key == ord('D'):
            bot.run_async(bot.dance)

        elif key == ord('Y'):
            bot.run_async(bot.all_actions)

        elif key == ord('T'):
            bot.run_async(lambda: bot.turn_and_speak("I am turning left while speaking!"))

        # Actions
        elif key == ord('W'):
            bot.run_async(bot.wave)
        elif key == ord('B'):
            bot.run_async(bot.blink_lights)
        elif key == ord('H'):
            bot.run_async(bot.say_hello)
        
        # Tasks
        elif key == ord('A'):
            print("\n📝 ADD TASK via API:")
            print("curl -X POST http://localhost:8000/command -H 'Content-Type: application/json' \\")
            print("-d '{\"action\":\"add_task\",\"task_name\":\"YOUR_TASK\",\"date\":\"2025-10-16\",\"time\":\"14:00\"}'")
            bot.run_async(lambda: bot.speak("Use API to add task. Check console."))
        
        elif key == ord('K'):
            bot.run_async(bot.list_tasks_vocal)
        
        elif key == ord('C'):
            bot.run_async(bot.clear_tasks)
        
        # System
        elif key == ord('S'):
            bot.stop_all()
        elif key == ord('Q'):
            print("👋 Quitting...")
            bot.stop_all()
            break

    print("🤖 Desk Buddy shutting down...")


if __name__ == "__main__":
    main()