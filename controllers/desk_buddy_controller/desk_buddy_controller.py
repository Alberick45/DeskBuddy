# ==========================================
# IMPORTS AND SETUP
# ==========================================
import threading  # For simultaneous action execution
import time       # For time.sleep() in threaded functions (replaces self.step())
from controller import Robot  # Webots Robot class

TIME_STEP = 32  # Simulation time step (milliseconds)
print("🤖 Robo Desk Buddy is alive!")

# ==========================================
# MAIN ROBOT CLASS
# ==========================================
class DeskBuddy(Robot):
    def __init__(self):
        """
        Initialize the DeskBuddy robot with devices and threading controls.
        
        Threading Architecture:
        - Main thread: Handles simulation stepping and keyboard input
        - Worker threads: Execute individual actions using time.sleep()
        - Thread safety: Uses locks to prevent device conflicts
        """
        super().__init__()
        
        # ==========================================
        # DEVICE INITIALIZATION
        # ==========================================
        # Get physical devices from the world file
        # These must exist as children of the Robot in Deskworld.wbt
        self.led_left = self.getDevice("eye_led_left")    # Left LED eye
        self.led_right = self.getDevice("eye_led_right")  # Right LED eye  
        self.motor = self.getDevice("tilt_motor")         # Head tilt motor
        self.motor.setPosition(0.0)                       # Reset to neutral position
        
        # Wheel motors for actual robot movement
        self.left_wheel = self.getDevice("left_wheel_motor")   # Left wheel motor
        self.right_wheel = self.getDevice("right_wheel_motor") # Right wheel motor
        
        # Set wheels to velocity control mode
        self.left_wheel.setPosition(float('inf'))
        self.right_wheel.setPosition(float('inf'))
        self.left_wheel.setVelocity(0.0)
        self.right_wheel.setVelocity(0.0)
        
        # ==========================================
        # THREADING CONTROL SYSTEM
        # ==========================================
        self.action_lock = threading.Lock()  # Prevents multiple threads from controlling devices simultaneously
        self.active_threads = []             # Track running threads for cleanup
        
        print("✅ DeskBuddy initialized with threading support")

    # ==========================================
    # THREADED ACTION METHODS
    # ==========================================
    # Key principle: NO self.step() calls in these methods!
    # Use time.sleep() instead to avoid simulation crashes
    
    def turn(self, direction, duration):
        """
        Thread-safe turn action - physically rotates robot left or right using wheel motors
        
        Parameters:
        - direction: 'left' or 'right'
        - duration: time in seconds to turn
        
        Physical Implementation:
        - Uses differential drive: opposite wheel directions create rotation
        - Left turn: left wheel backward, right wheel forward
        - Right turn: left wheel forward, right wheel backward
        """
        print(f"🔄 Turning {direction} for {duration} seconds...")
        
        # Set wheel velocities for turning
        turn_speed = 2.0  # Rotation speed
        
        with self.action_lock:
            if direction.lower() == 'left':
                # Left turn: left wheel backward, right wheel forward
                self.left_wheel.setVelocity(-turn_speed)
                self.right_wheel.setVelocity(turn_speed)
            elif direction.lower() == 'right':
                # Right turn: left wheel forward, right wheel backward
                self.left_wheel.setVelocity(turn_speed)
                self.right_wheel.setVelocity(-turn_speed)
        
        # Turn for specified duration
        time.sleep(duration)
        
        # Stop wheels after turning
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
        
        print(f"🔄 Turn {direction} complete!")

    def speak(self, message):
        """
        Thread-safe speak action - prints message with visual LED feedback
        
        Parameters:
        - message: The string message to "speak"
        
        Enhanced Features:
        - LED eyes blink while speaking to show activity
        - Speech timing based on message length
        - Visual feedback enhances the speaking experience
        """
        print(f"🗣️ Speaking: '{message}'")
        
        # Calculate speaking duration based on message length (more realistic)
        words = len(message.split())
        speak_duration = max(1.0, words * 0.3)  # ~0.3 seconds per word, minimum 1 second
        
        # Blink LEDs while speaking to show activity
        blink_interval = 0.5  # Blink every 0.5 seconds
        elapsed_time = 0.0
        
        while elapsed_time < speak_duration:
            # Turn LEDs on
            with self.action_lock:
                self.led_left.set(1)
                self.led_right.set(1)
            
            time.sleep(min(blink_interval/2, speak_duration - elapsed_time))
            elapsed_time += blink_interval/2
            
            if elapsed_time >= speak_duration:
                break
                
            # Turn LEDs off  
            with self.action_lock:
                self.led_left.set(0)
                self.led_right.set(0)
            
            time.sleep(min(blink_interval/2, speak_duration - elapsed_time))
            elapsed_time += blink_interval/2
        
        # Ensure LEDs are off when done speaking
        with self.action_lock:
            self.led_left.set(0)
            self.led_right.set(0)
        
        print("🗣️ Speak action complete!")

    def move_forward(self, duration=2.0):
        """
        Thread-safe forward movement - moves robot straight ahead
        
        Parameters:
        - duration: time in seconds to move forward
        
        Physical Implementation:
        - Both wheels rotate in same direction at same speed
        - Creates straight-line forward movement
        """
        print(f"➡️ Moving forward for {duration} seconds...")
        
        move_speed = 2.0  # Forward movement speed
        
        # Both wheels forward at same speed
        with self.action_lock:
            self.left_wheel.setVelocity(move_speed)
            self.right_wheel.setVelocity(move_speed)
        
        # Move for specified duration
        time.sleep(duration)
        
        # Stop wheels
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
        
        print("➡️ Forward movement complete!")

    def move_backward(self, duration=2.0):
        """
        Thread-safe backward movement - moves robot straight back
        
        Parameters:
        - duration: time in seconds to move backward
        """
        print(f"⬅️ Moving backward for {duration} seconds...")
        
        move_speed = 2.0  # Backward movement speed
        
        # Both wheels backward at same speed
        with self.action_lock:
            self.left_wheel.setVelocity(-move_speed)
            self.right_wheel.setVelocity(-move_speed)
        
        # Move for specified duration
        time.sleep(duration)
        
        # Stop wheels
        with self.action_lock:
            self.left_wheel.setVelocity(0.0)
            self.right_wheel.setVelocity(0.0)
        
        print("⬅️ Backward movement complete!")


    def wave(self):
        """
        Thread-safe wave action - tilts head left and right
        
        Threading Notes:
        - Uses action_lock to prevent device conflicts
        - Uses time.sleep() instead of self.step()
        - Can run simultaneously with other actions
        """
        print("👋 Waving...")
        
        # Step 1: Tilt head right (0.5 radians)
        with self.action_lock:  # Lock ensures only one thread modifies motor at a time
            self.motor.setPosition(0.5)
        time.sleep(0.5)  # Wait 0.5 seconds (NOT self.step()!)
        
        # Step 2: Tilt head left (-0.5 radians)
        with self.action_lock:
            self.motor.setPosition(-0.5)
        time.sleep(0.5)
        
        # Step 3: Return to center (0.0 radians)
        with self.action_lock:
            self.motor.setPosition(0.0)
        time.sleep(0.5)
        
        print("👋 Wave complete!")

    def blink_lights(self):
        """
        Thread-safe LED blinking - flashes both eyes 3 times
        
        Threading Notes:
        - Controls both LEDs simultaneously
        - Independent timing from other actions
        - Thread-safe device access with locks
        """
        print("✨ Blinking LEDs...")
        
        for i in range(3):  # Blink 3 times
            # Turn LEDs ON
            with self.action_lock:
                self.led_left.set(1)   # 1 = LED on
                self.led_right.set(1)  # 1 = LED on
            time.sleep(0.3)  # Keep on for 0.3 seconds
            
            # Turn LEDs OFF
            with self.action_lock:
                self.led_left.set(0)   # 0 = LED off
                self.led_right.set(0)  # 0 = LED off
            time.sleep(0.3)  # Keep off for 0.3 seconds
            
            print(f"✨ Blink {i+1}/3 complete")
        
        print("✨ All blinks complete!")

    def say_hello(self):
        """
        Thread-safe hello action - prints greeting messages
        
        Note: This is a placeholder for actual movement.
        In a real implementation, this would control wheel motors
        to make the robot move forward while greeting.
        """
        print("🗣️ Hello! I'm your Robo Desk Buddy!")
        
        for i in range(3):
            print(f"➡️ Moving forward (step {i+1}/3)")
            time.sleep(0.2)  # Short delay between messages
        
        print("🗣️ Hello sequence complete!")


    def patrol_mode(self):
        """Continuous patrol with head scanning"""
        for _ in range(5):  # Patrol 5 cycles
            print("🚶 Patrolling...")
            # Move forward (placeholder)
            time.sleep(1.0)
            # Scan left
            with self.action_lock:
                self.motor.setPosition(0.7)
            time.sleep(0.5)
            # Scan right  
            with self.action_lock:
                self.motor.setPosition(-0.7)
            time.sleep(0.5)

    def dance_sequence(self):
        """Coordinated dance with lights and movement"""
        for beat in range(4):
            # Head movement
            with self.action_lock:
                self.motor.setPosition(0.5 if beat % 2 == 0 else -0.5)
            # Light flash
            with self.action_lock:
                self.led_left.set(beat % 2)
                self.led_right.set((beat + 1) % 2)
            time.sleep(0.8)
    # ==========================================
    # THREADING MANAGEMENT SYSTEM
    # ==========================================
    
    def run_async(self, func):
        """
        Execute any function in a separate thread with automatic cleanup
        
        Parameters:
        - func: The function to run in a thread (e.g., self.wave)
        
        Returns:
        - thread: The created thread object
        
        Threading Flow:
        1. Create wrapper function that handles errors and cleanup
        2. Create new thread with the wrapper
        3. Add thread to active_threads list for tracking
        4. Start the thread (non-blocking)
        5. Return thread object for reference
        """
        def wrapper():
            """Internal wrapper that handles thread lifecycle"""
            try:
                func()  # Execute the actual action function
            except Exception as e:
                print(f"❌ Thread error in {func.__name__}: {e}")
            finally:
                # Clean up: Remove this thread from active list when done
                with self.action_lock:  # Thread-safe list modification
                    if threading.current_thread() in self.active_threads:
                        self.active_threads.remove(threading.current_thread())
                print(f"🧹 Thread {func.__name__} cleaned up")
        
        # Create and start the thread
        thread = threading.Thread(target=wrapper, name=f"Thread-{func.__name__}")
        
        # Track the thread
        with self.action_lock:  # Thread-safe list modification
            self.active_threads.append(thread)
        
        thread.start()  # Start thread (non-blocking)
        print(f"🚀 Started thread for {func.__name__}")
        return thread

    def stop_all_actions(self):
        """
        Emergency stop - reset all devices to neutral state
        
        Note: Python threading doesn't allow forceful thread termination,
        so this only resets the hardware devices. Threads will complete
        their current sleep cycles naturally.
        
        Best Practice: Design actions to check a "stop_flag" periodically
        """
        print("🛑 Stopping all actions...")
        
        # Reset all devices to neutral/off state
        with self.action_lock:
            self.motor.setPosition(0.0)      # Head to center
            self.led_left.set(0)             # LEDs off
            self.led_right.set(0)            # LEDs off
            self.left_wheel.setVelocity(0.0) # Stop left wheel
            self.right_wheel.setVelocity(0.0)# Stop right wheel
        
        print(f"🧹 Active threads: {len(self.active_threads)}")
        print("⚠️ Note: Threads will complete their current sleep cycles")

# ==========================================
# MAIN CONTROL LOOP
# ==========================================
def main():
    """
    Main simulation loop - handles keyboard input and coordinates actions
    
    Threading Architecture:
    - This function runs in the MAIN THREAD
    - Only the main thread calls bot.step() - critical for simulation stability
    - All actions are executed in separate worker threads
    - Keyboard input is processed in the main thread for responsiveness
    """
    # Initialize robot and devices
    bot = DeskBuddy()
    keyboard = bot.getKeyboard()
    keyboard.enable(TIME_STEP)

    # Display controls
    print("=" * 60)
    print("🎮 DESKBUDDY ROBOT CONTROLS:")
    print("  W = Wave (head tilt)")
    print("  B = Blink LEDs") 
    print("  H = Say Hello (text messages)")
    print("  P = Patrol Mode (head scanning)")
    print("  D = Begin Salsa Dance")
    print("  Y = ALL ACTIONS SIMULTANEOUSLY! 🎭")
    print("  T = Turn Left & Speak")
    print("  F = Move Forward")
    print("  R = Move Backward")
    print("  L = Turn Left")
    print("  G = Turn Right") 
    print("  S = Stop/Reset all actions")
    print("  Q = Quit simulation")
    print("=" * 60)

    # ==========================================
    # MAIN SIMULATION LOOP
    # ==========================================
    while bot.step(TIME_STEP) != -1:  # CRITICAL: Only main thread calls step()
        key = keyboard.getKey()
        
        # Process individual actions (each starts a new thread)
        if key == ord('W'):
            print("🔄 Starting wave action in new thread...")
            bot.run_async(bot.wave)
            
        elif key == ord('B'):
            print("🔄 Starting blink action in new thread...")
            bot.run_async(bot.blink_lights)

        elif key == ord('H'):
            print("🔄 Starting hello action in new thread...")
            bot.run_async(bot.say_hello)
    
        elif key == ord('D'):
            print("🔄 Starting dance action in new thread...")
            bot.run_async(bot.dance_sequence)

        elif key == ord('P'):
            print("🔄 Starting patrol mode in new thread...")
            bot.run_async(bot.patrol_mode)
        
        # ==========================================
        # MOVEMENT CONTROLS
        # ==========================================
        elif key == ord('F'):
            print("🔄 Starting forward movement in new thread...")
            bot.run_async(lambda: bot.move_forward(2.0))
            
        elif key == ord('R'):
            print("🔄 Starting backward movement in new thread...")
            bot.run_async(lambda: bot.move_backward(2.0))
            
        elif key == ord('L'):
            print("🔄 Starting left turn in new thread...")
            bot.run_async(lambda: bot.turn('left', 1.5))
            
        elif key == ord('G'):
            print("🔄 Starting right turn in new thread...")
            bot.run_async(lambda: bot.turn('right', 1.5))
        
        # ==========================================
        # SIMULTANEOUS ACTIONS DEMO
        # ==========================================
        elif key == ord('Y'):
            print("🎭 SIMULTANEOUS ACTIONS DEMO!")
            print("🚀 Starting ALL actions in parallel threads...")
            
            # Start all three actions simultaneously
            # Each runs in its own thread with independent timing
            thread1 = bot.run_async(bot.say_hello)    # ~0.6 seconds total
            thread2 = bot.run_async(bot.blink_lights) # ~1.8 seconds total  
            thread3 = bot.run_async(bot.wave)         # ~1.5 seconds total
            
            print(f"✅ Started {len(bot.active_threads)} simultaneous threads!")
            print("👀 Watch: Head waves + LEDs blink + hello messages all at once!")



        elif key == ord('T'):
            print("🎭 TURN AND SPEAK DEMO!")
            print("🚀 Starting turn and speak actions in parallel threads...")
            
            # Start turn and speak actions with proper parameters
            thread1 = bot.run_async(lambda: bot.turn('left', 2.0))    # Turn left for 2 seconds
            thread2 = bot.run_async(lambda: bot.speak('Hello! I am turning left now!')) # Speak message
            
            print(f"✅ Started {len(bot.active_threads)} simultaneous threads!")
            print("👀 Watch: Robot turns left while speaking!")


            
        # ==========================================
        # EMERGENCY CONTROLS
        # ==========================================
        elif key == ord('S'):
            bot.stop_all_actions()
            
        elif key == ord('Q'):
            print("🛑 Quitting simulation...")
            bot.stop_all_actions()
            break
        
        # Debug: Show unknown keys
        elif key != -1:
            print(f"❓ Unknown key pressed: {chr(key)} (code: {key})")

    print("🤖 Desk Buddy shutting down...")
    print(f"🧹 Final cleanup: {len(bot.active_threads)} threads still active")

# ==========================================
# ENTRY POINT
# ==========================================
if __name__ == "__main__":
    main()