import threading
import time
import requests
from controller import Robot, Keyboard
from flask import Flask, request, jsonify

TIME_STEP = 32


# ==========================================
# FLASK APP SETUP
# ==========================================
app = Flask(__name__)
robot_instance = None  # Shared between Webots and Flask


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
    print(f"[API] Received: {action}, duration={duration}, message={message}")

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
        robot_instance.add_task(message)
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
        self.api_url = "http://localhost:5000/api/tasks"  # your external task API

        # Get devices from world file
        self.led_left = self.getDevice("eye_led_left")
        self.led_right = self.getDevice("eye_led_right")
        self.speaker = self.getDevice("speaker")
        self.speaker.setLanguage("en-US")
        self.head_motor = self.getDevice("tilt_motor")
        self.head_motor.setPosition(0.0)

        #hands 
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
        #legs
        self.left_leg = self.getDevice("left_leg_motor")
        self.right_leg = self.getDevice("right_leg_motor")
        self.left_leg.setPosition(float('inf'))
        self.right_leg.setPosition(float('inf'))
        self.left_leg.setVelocity(0.0)
        self.right_leg.setVelocity(0.0)
        #end
        
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
        """Add a task and sync to external API."""
        if not task:
            print("⚠️ No task provided.")
            return

        with self.action_lock:
            self.tasks.append(task)
        print(f"✅ Task added: {task}")

        self.run_async(lambda: self.speak(f"Task added: {task}"))
        self.send_task_to_api(task)

    def list_tasks(self):
        """List all current tasks."""
        with self.action_lock:
            if not self.tasks:
                self.run_async(lambda: self.speak("You have no tasks."))
                return []
            self.run_async(lambda: self.speak(f"You have {len(self.tasks)} tasks."))
            for i, task in enumerate(self.tasks, start=1):
                print(f"{i}. {task}")
            return self.tasks

    def remove_task(self, index):
        """Remove a task by index."""
        with self.action_lock:
            if 0 <= index < len(self.tasks):
                removed = self.tasks.pop(index)
                print(f"🗑️ Removed task: {removed}")
                self.run_async(lambda: self.speak(f"Removed task: {removed}"))
                return removed
            else:
                print("⚠️ Invalid index for removal.")
                self.run_async(lambda: self.speak("Invalid task number."))
                return None

    def clear_tasks(self):
        """Clear all tasks."""
        with self.action_lock:
            self.tasks.clear()
        print("🧹 All tasks cleared.")
        self.run_async(lambda: self.speak("All tasks cleared."))

    def send_task_to_api(self, task):
        """Send the task to an external API."""
        try:
            payload = {"task": task}
            response = requests.post(self.api_url, json=payload, timeout=5)
            if response.status_code == 200:
                print(f"🌐 Synced task successfully: {response.json()}")
            else:
                print(f"⚠️ API sync failed ({response.status_code})")
        except Exception as e:
            print(f"🚫 Could not reach API: {e}")
    # ==========================================
    # DIRECT MOVEMENT CONTROL (No threading)
    # ==========================================
    def move_forward_c(self):
        """Move forward at max speed"""
        with self.action_lock:
            self.left_wheel.setVelocity(self.max_speed)
            self.right_wheel.setVelocity(self.max_speed)
            self.left_rear_wheel.setVelocity(self.max_speed)
            self.right_rear_wheel.setVelocity(self.max_speed)

    def move_backward_c(self):
        """Move backward at max speed"""
        with self.action_lock:
            self.left_wheel.setVelocity(-self.max_speed)
            self.right_wheel.setVelocity(-self.max_speed)
            self.left_rear_wheel.setVelocity(-self.max_speed)
            self.right_rear_wheel.setVelocity(-self.max_speed)

    def turn_left_c(self):
        """Turn left in place"""
        with self.action_lock:
            self.left_wheel.setVelocity(-self.turn_speed)
            self.right_wheel.setVelocity(self.turn_speed)
            self.left_rear_wheel.setVelocity(-self.turn_speed)
            self.right_rear_wheel.setVelocity(self.turn_speed)

    def turn_right_c(self):
        """Turn right in place"""
        with self.action_lock:
            self.left_wheel.setVelocity(self.turn_speed)
            self.right_wheel.setVelocity(-self.turn_speed)
            self.left_rear_wheel.setVelocity(self.turn_speed)
            self.right_rear_wheel.setVelocity(-self.turn_speed)

    def stop_c(self):
        """Stop all wheel movement"""
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)

    # ==========================================
    # THREADED ACTIONS
    # ==========================================
    def turn(self, direction, duration):
        """Turn robot left or right for specified duration - FIXED TO CONTROL ALL 4 WHEELS"""
        print(f"Turning {direction} for {duration} seconds...")
        
        turn_speed = 2.0
        
        with self.action_lock:
            if direction.lower() == 'left':
                # Left side wheels backward, right side wheels forward
                self.left_wheel.setVelocity(-turn_speed)
                self.right_wheel.setVelocity(turn_speed)
                self.left_rear_wheel.setVelocity(-turn_speed)
                self.right_rear_wheel.setVelocity(turn_speed)
            elif direction.lower() == 'right':
                # Left side wheels forward, right side wheels backward
                self.left_wheel.setVelocity(turn_speed)
                self.right_wheel.setVelocity(-turn_speed)
                self.left_rear_wheel.setVelocity(turn_speed)
                self.right_rear_wheel.setVelocity(-turn_speed)
        
        time.sleep(duration)
        
        # Stop all wheels
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)
        
        print(f"Turn {direction} complete!")

    def speak(self, message):
        """Speak message with LED animation"""
        print(f"Speaking: '{message}'")

        try:
            self.speaker.speak(message, 1.0)
        except Exception as e:
            print(f"Could not use speaker: {e}")
        
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

        print("Speak action complete!")

    def move_forward(self, duration=2.0):
        """Move robot forward"""
        print(f"Moving forward for {duration} seconds...")
        
        move_speed = 2.0
        
        with self.action_lock:
            self.left_wheel.setVelocity(move_speed)
            self.right_wheel.setVelocity(move_speed)
            self.left_rear_wheel.setVelocity(move_speed)
            self.right_rear_wheel.setVelocity(move_speed)
        
        time.sleep(duration)
        
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)
        
        print("Forward movement complete!")

    def move_backward(self, duration=2.0):
        """Move robot backward"""
        print(f"Moving backward for {duration} seconds...")
        
        move_speed = 2.0
        
        with self.action_lock:
            self.left_wheel.setVelocity(-move_speed)
            self.right_wheel.setVelocity(-move_speed)
            self.left_rear_wheel.setVelocity(-move_speed)
            self.right_rear_wheel.setVelocity(-move_speed)
        
        time.sleep(duration)
        
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)
        
        print("Backward movement complete!")

    def wave(self):
        """Wave head left and right"""
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
            self.head_motor.setPosition(0.2)
            self.right_hand_motor.setPosition(0.0)
        time.sleep(0.5)
        
        print("Wave complete!")

    def blink_lights(self):
        """Blink LEDs 3 times"""
        print("Blinking LEDs...")
        
        for i in range(3):
            with self.action_lock:
                self.led_left.set(1)
                self.led_right.set(1)
            time.sleep(0.3)
            
            with self.action_lock:
                self.led_left.set(0)
                self.led_right.set(0)
            time.sleep(0.3)
            
            print(f"Blink {i+1}/3 complete")
        
        print("All blinks complete!")

    def say_hello(self):
        """Say hello message"""
        self.speak("Hello! I'm your Robo Desk Buddy!")

    def patrol_mode(self):
        """Patrol mode: Robot moves in a square pattern while scanning head"""
        print("Starting patrol mode...")
        
        patrol_cycles = 3  # Number of complete squares to patrol
        
        for cycle in range(patrol_cycles):
            print(f"Patrol cycle {cycle + 1}/{patrol_cycles}")
            
            # Move forward while scanning head
            print("Moving forward and scanning...")
            self.move_forward()
            time.sleep(2.0)
            
            # Scan head while moving forward
            for _ in range(4):
                with self.action_lock:
                    self.head_motor.setPosition(0.7)
                time.sleep(0.3)
                with self.action_lock:
                    self.head_motor.setPosition(-0.7)
                time.sleep(0.3)
            
            # Stop movement
            self.stop_all_actions()
            time.sleep(0.5)
            
            # Turn right using the turn_right_c method
            print("Turning right...")
            self.turn('right', 2.0)
            time.sleep(2.0)
            
            # Reset head to center
            with self.action_lock:
                self.head_motor.setPosition(0.0)
        
        # Final stop and center head
        print("Patrol complete!")
        self.stop_all_actions()
        with self.action_lock:
            self.head_motor.setPosition(0.0)

    def dance_sequence(self):
        """Dance with lights and head movement"""
        for beat in range(4):
            with self.action_lock:
                self.head_motor.setPosition(0.5 if beat % 2 == 0 else -0.5)
                self.led_left.set(beat % 2)
                self.led_right.set((beat + 1) % 2)
            time.sleep(0.8)

    # ==========================================
    # THREADING MANAGEMENT
    # ==========================================
    def run_async(self, func):
        """Execute function in separate thread"""
        def wrapper():
            try:
                func()
            except Exception as e:
                print(f"Thread error in {func.__name__}: {e}")
            finally:
                with self.action_lock:
                    if threading.current_thread() in self.active_threads:
                        self.active_threads.remove(threading.current_thread())
                print(f"Thread {func.__name__} cleaned up")
        
        thread = threading.Thread(target=wrapper, name=f"Thread-{func.__name__}")
        
        with self.action_lock:
            self.active_threads.append(thread)
        
        thread.start()
        print(f"Started thread for {func.__name__}")
        return thread

    def stop_all_actions(self):
        """Emergency stop - reset all devices"""
        print("Stopping all actions...")
        
        with self.action_lock:
            self.head_motor.setPosition(0.0)
            self.led_left.set(0)
            self.led_right.set(0)
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)
        
        print(f"Active threads: {len(self.active_threads)}")


def main():
    """Main control loop"""
    global robot_instance
    bot = DeskBuddy()
    robot_instance = bot

    keyboard = bot.getKeyboard()
    keyboard.enable(TIME_STEP)

    # Start Flask API server in background thread
    api_thread = threading.Thread(target=start_api_server, daemon=True)
    api_thread.start()

    print("=" * 60)
    print("DESKBUDDY ROBOT CONTROLS:")
    print("  W = Wave")
    print("  B = Blink LEDs")
    print("  H = Say Hello")
    print("  P = Patrol Mode")
    print("  D = Dance")
    print("  Y = All Actions Simultaneously")
    print("  T = Turn Left & Speak")
    print("  F = Move Forward")
    print("  R = Move Backward")
    print("  L = Turn Left")
    print("  G = Turn Right")
    print("  Space = Stop Movement")
    print("  S = Stop/Reset All")
    print("  Q = Quit")
    print("=" * 60)

    while bot.step(TIME_STEP) != -1:
        key = keyboard.getKey()
        
        if key == ord('W'):
            bot.run_async(bot.wave)
            
        elif key == ord('B'):
            bot.run_async(bot.blink_lights)

        elif key == ord('H'):
            bot.run_async(bot.say_hello)
    
        elif key == ord('D'):
            bot.run_async(bot.dance_sequence)

        elif key == ord('P'):
            bot.run_async(bot.patrol_mode)
        
        elif key == ord('F'):
            bot.move_forward_c()
        elif key == ord('R'):
            bot.move_backward_c()
        elif key == ord('L'):
            bot.turn_left_c()
        elif key == ord('G'):
            bot.turn_right_c()
        elif key == ord(' '):
            bot.stop_c()
        
        elif key == ord('Y'):
            print("Starting all actions simultaneously...")
            bot.run_async(bot.say_hello)
            bot.run_async(bot.blink_lights)
            bot.run_async(bot.wave)
            print(f"Started {len(bot.active_threads)} threads!")

        elif key == ord('T'):
            print("Turn and speak demo...")
            bot.run_async(lambda: bot.turn('left', 2.0))
            bot.run_async(lambda: bot.speak('Hello! I am turning left now!'))
            print(f"Started {len(bot.active_threads)} threads!")
            
        elif key == ord('S'):
            bot.stop_all_actions()
            
        elif key == ord('Q'):
            print("Quitting simulation...")
            bot.stop_all_actions()
            break
        
        elif key != -1:
            print(f"Unknown key: {chr(key)}")

    print("Desk Buddy shutting down...")
    print(f"Final cleanup: {len(bot.active_threads)} threads still active")


if __name__ == "__main__":
    main()