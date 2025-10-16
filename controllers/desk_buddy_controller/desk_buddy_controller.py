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
    elif action == "stop":
        robot_instance.stop_all_actions()

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
        tasks = robot_instance.list_tasks()
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
    app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False)


class DeskBuddy(Robot):
    def __init__(self):
        super().__init__()
        
        # Threading control
        self.action_lock = threading.Lock()
        self.active_threads = []
        
        # Task management
        self.tasks = []
        self.api_url = "http://localhost:5000/api/tasks"

        # Get devices from world file
        self.led_left = self.getDevice("eye_led_left")
        self.led_right = self.getDevice("eye_led_right")
        self.speaker = self.getDevice("speaker")
        self.speaker.setLanguage("en-US")
        self.head_motor = self.getDevice("tilt_motor")
        self.head_motor.setPosition(0.0)

        # Hands 
        self.left_hand_motor = self.getDevice("left_arm_motor")
        self.left_hand_motor.setPosition(0.0)
        self.right_hand_motor = self.getDevice("right_arm_motor")
        self.right_hand_motor.setPosition(0.0)
        
        # Wheel motors
        self.left_wheel = self.getDevice("left_wheel_motor")
        self.right_wheel = self.getDevice("right_wheel_motor")
        self.left_wheel.setPosition(float('inf'))
        self.right_wheel.setPosition(float('inf'))
        self.left_wheel.setVelocity(0.0)
        self.right_wheel.setVelocity(0.0)
        
        self.left_rear_wheel = self.getDevice("left_rear_wheel_motor")
        self.right_rear_wheel = self.getDevice("right_rear_wheel_motor")
        self.left_rear_wheel.setPosition(float('inf'))
        self.right_rear_wheel.setPosition(float('inf'))
        self.left_rear_wheel.setVelocity(0.0)
        self.right_rear_wheel.setVelocity(0.0)
        
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
            self.run_async(lambda: self.speak("Error: No task name provided."))
            return

        with self.action_lock:
            self.tasks.append(task)
        
        task_info = f"{task['name']} on {task.get('date', 'no date')} at {task.get('time', 'no time')}"
        print(f"✅ Task added: {task_info}")
        
        self.run_async(lambda: self.speak(f"Task added: {task['name']}"))
        self.send_task_to_api(task)

    def list_tasks(self):
        """List all current tasks."""
        with self.action_lock:
            if not self.tasks:
                print("📋 No tasks available.")
                self.run_async(lambda: self.speak("You have no tasks."))
                return []
            
            print(f"📋 You have {len(self.tasks)} tasks:")
            for i, task in enumerate(self.tasks, start=1):
                task_str = f"{i}. {task.get('name', 'Unnamed')} - {task.get('date', 'No date')} at {task.get('time', 'No time')}"
                print(task_str)
            
            self.run_async(lambda: self.speak(f"You have {len(self.tasks)} tasks."))
            return self.tasks

    def remove_task(self, index):
        """Remove a task by index."""
        with self.action_lock:
            if 0 <= index < len(self.tasks):
                removed = self.tasks.pop(index)
                print(f"🗑️ Removed task: {removed.get('name', 'Unnamed')}")
                self.run_async(lambda: self.speak(f"Removed task: {removed.get('name', 'Task')}"))
                return removed
            else:
                print("⚠️ Invalid index for removal.")
                self.run_async(lambda: self.speak("Invalid task number."))
                return None

    def clear_tasks(self):
        """Clear all tasks."""
        with self.action_lock:
            count = len(self.tasks)
            self.tasks.clear()
        print(f"🧹 Cleared {count} tasks.")
        self.run_async(lambda: self.speak(f"Cleared {count} tasks."))

    def send_task_to_api(self, task):
        """Send the task to an external API."""
        try:
            response = requests.post(self.api_url, json=task, timeout=5)
            if response.status_code == 200:
                print(f"🌐 Synced task successfully")
            else:
                print(f"⚠️ API sync failed ({response.status_code})")
        except Exception as e:
            print(f"🚫 Could not reach API: {e}")

    # ==========================================
    # DIRECT MOVEMENT CONTROL
    # ==========================================
    def move_forward_c(self):
        with self.action_lock:
            self.left_wheel.setVelocity(self.max_speed)
            self.right_wheel.setVelocity(self.max_speed)
            self.left_rear_wheel.setVelocity(self.max_speed)
            self.right_rear_wheel.setVelocity(self.max_speed)

    def move_backward_c(self):
        with self.action_lock:
            self.left_wheel.setVelocity(-self.max_speed)
            self.right_wheel.setVelocity(-self.max_speed)
            self.left_rear_wheel.setVelocity(-self.max_speed)
            self.right_rear_wheel.setVelocity(-self.max_speed)

    def turn_left_c(self):
        with self.action_lock:
            self.left_wheel.setVelocity(-self.turn_speed)
            self.right_wheel.setVelocity(self.turn_speed)
            self.left_rear_wheel.setVelocity(-self.turn_speed)
            self.right_rear_wheel.setVelocity(self.turn_speed)

    def turn_right_c(self):
        with self.action_lock:
            self.left_wheel.setVelocity(self.turn_speed)
            self.right_wheel.setVelocity(-self.turn_speed)
            self.left_rear_wheel.setVelocity(self.turn_speed)
            self.right_rear_wheel.setVelocity(-self.turn_speed)

    def stop_c(self):
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)

    # ==========================================
    # THREADED ACTIONS
    # ==========================================
    def turn(self, direction, duration):
        print(f"Turning {direction} for {duration} seconds...")
        turn_speed = 2.0
        
        with self.action_lock:
            if direction.lower() == 'left':
                self.left_wheel.setVelocity(-turn_speed)
                self.right_wheel.setVelocity(turn_speed)
                self.left_rear_wheel.setVelocity(-turn_speed)
                self.right_rear_wheel.setVelocity(turn_speed)
            elif direction.lower() == 'right':
                self.left_wheel.setVelocity(turn_speed)
                self.right_wheel.setVelocity(-turn_speed)
                self.left_rear_wheel.setVelocity(turn_speed)
                self.right_rear_wheel.setVelocity(-turn_speed)
        
        time.sleep(duration)
        
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)

    def speak(self, message):
        print(f"Speaking: '{message}'")
        try:
            self.speaker.speak(message, 1.0)
        except Exception as e:
            print(f"Could not use speaker: {e}")
        
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

    def move_forward(self, duration=2.0):
        print(f"Moving forward for {duration} seconds...")
        with self.action_lock:
            self.left_wheel.setVelocity(2.0)
            self.right_wheel.setVelocity(2.0)
            self.left_rear_wheel.setVelocity(2.0)
            self.right_rear_wheel.setVelocity(2.0)
        time.sleep(duration)
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)

    def move_backward(self, duration=2.0):
        print(f"Moving backward for {duration} seconds...")
        with self.action_lock:
            self.left_wheel.setVelocity(-2.0)
            self.right_wheel.setVelocity(-2.0)
            self.left_rear_wheel.setVelocity(-2.0)
            self.right_rear_wheel.setVelocity(-2.0)
        time.sleep(duration)
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)

    def wave(self):
        print("Waving...")
        with self.action_lock:
            self.head_motor.setPosition(0.2)
            self.right_hand_motor.setPosition(0.5)
        time.sleep(0.5)
        with self.action_lock:
            self.head_motor.setPosition(-0.2)
            self.right_hand_motor.setPosition(-0.5)
        time.sleep(0.5)
        with self.action_lock:
            self.head_motor.setPosition(0.0)
            self.right_hand_motor.setPosition(0.0)

    def blink_lights(self):
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

    def run_async(self, func):
        def wrapper():
            try:
                func()
            except Exception as e:
                print(f"Thread error: {e}")
            finally:
                with self.action_lock:
                    if threading.current_thread() in self.active_threads:
                        self.active_threads.remove(threading.current_thread())
        
        thread = threading.Thread(target=wrapper)
        with self.action_lock:
            self.active_threads.append(thread)
        thread.start()
        return thread

    def stop_all_actions(self):
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
    print("DESKBUDDY ROBOT CONTROLS:")
    print("  MOVEMENT:")
    print("    F = Move Forward | R = Move Backward")
    print("    L = Turn Left    | G = Turn Right    | Space = Stop")
    print("  ACTIONS:")
    print("    W = Wave | B = Blink | H = Say Hello")
    print("  TASKS (via API):")
    print("    A = Add Task (opens API instructions)")
    print("    K = List Tasks")
    print("    C = Clear All Tasks")
    print("  OTHER:")
    print("    S = Stop All | Q = Quit")
    print("=" * 70)
    print("\n📡 API ENDPOINT: http://localhost:8000/command")
    print("Example: curl -X POST http://localhost:8000/command -H 'Content-Type: application/json' -d '{\"action\":\"add_task\",\"task_name\":\"Meeting\",\"date\":\"2025-10-16\",\"time\":\"14:00\"}'")
    print("=" * 70)

    while bot.step(TIME_STEP) != -1:
        key = keyboard.getKey()
        
        # Movement
        if key == ord('F'):
            bot.move_forward_c()
        elif key == ord('R'):
            bot.move_backward_c()
        elif key == ord('L'):
            bot.turn_left_c()
        elif key == ord('G'):
            bot.turn_right_c()
        elif key == ord(' '):
            bot.stop_c()
        
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
            bot.run_async(lambda: bot.speak("Use API to add task. Check console for instructions."))
        
        elif key == ord('K'):
            bot.list_tasks()
        
        elif key == ord('C'):
            bot.clear_tasks()
        
        # System
        elif key == ord('S'):
            bot.stop_all_actions()
        elif key == ord('Q'):
            print("Quitting...")
            bot.stop_all_actions()
            break

    print("Desk Buddy shutting down...")


if __name__ == "__main__":
    main()