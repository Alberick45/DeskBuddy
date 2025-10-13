import threading
import time
from controller import Robot, Keyboard

TIME_STEP = 32

class DeskBuddy(Robot):
    def __init__(self):
        super().__init__()
        
        # Threading control
        self.action_lock = threading.Lock()
        self.active_threads = []
        
        # Get devices from world file
        self.led_left = self.getDevice("eye_led_left")
        self.led_right = self.getDevice("eye_led_right")
        self.speaker = self.getDevice("speaker")
        self.speaker.setLanguage("en-US")
        self.motor = self.getDevice("tilt_motor")
        self.motor.setPosition(0.0)
        
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
            self.motor.setPosition(0.5)
        time.sleep(0.5)
        
        with self.action_lock:
            self.motor.setPosition(-0.5)
        time.sleep(0.5)
        
        with self.action_lock:
            self.motor.setPosition(0.0)
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
        """Patrol with head scanning"""
        for _ in range(5):
            print("Patrolling...")
            time.sleep(1.0)
            with self.action_lock:
                self.motor.setPosition(0.7)
            time.sleep(0.5)
            with self.action_lock:
                self.motor.setPosition(-0.7)
            time.sleep(0.5)

    def dance_sequence(self):
        """Dance with lights and head movement"""
        for beat in range(4):
            with self.action_lock:
                self.motor.setPosition(0.5 if beat % 2 == 0 else -0.5)
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
            self.motor.setPosition(0.0)
            self.led_left.set(0)
            self.led_right.set(0)
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
            self.left_rear_wheel.setVelocity(0.0)
            self.right_rear_wheel.setVelocity(0.0)
        
        print(f"Active threads: {len(self.active_threads)}")


def main():
    """Main control loop"""
    bot = DeskBuddy()
    keyboard = bot.getKeyboard()
    keyboard.enable(TIME_STEP)

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