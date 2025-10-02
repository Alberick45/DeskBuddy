from controller import Robot

# Time step
TIME_STEP = 32

print("🤖 Robo Desk Buddy is alive!")

# Define robot class
class DeskBuddy(Robot):
    def __init__(self):
        super().__init__()  # Initialize Robot base class

        # Devices
        self.led_left = self.getDevice("eye_led_left")
        self.led_right = self.getDevice("eye_led_right")
        self.motor = self.getDevice("tilt_motor")

        # Reset motor position
        self.motor.setPosition(0.0)

    # --- Actions ---
    def move_forward(self):
        for _ in range(3):
            print("➡️ Moving forward")

    def move_backward(self):
        print("⬅️ Moving backward")

    def move_left(self):
        print("⬆️ Moving left")

    def move_right(self):
        print("⬇️ Moving right")    

    def wave(self):
        """Make the robot tilt as a wave gesture."""
        print("👋 Waving...")
        self.motor.setPosition(0.5)   # tilt right
        self.step(500)                # wait 0.5 sec
        self.motor.setPosition(-0.5)  # tilt left
        self.step(500)
        self.motor.setPosition(0.0)   # reset
        self.step(500)

    def blink_lights(self):
        """Blink LED on and off."""
        print("✨ Blinking LEDs...")
        for _ in range(3):
            self.led_left.set(1)   # on
            self.led_right.set(1)   # on
            self.step(300)
            self.led_left.set(0)   # off
            self.led_right.set(0)   # off
            self.step(300)

    def say_hello(self):
        """Print a hello message (later could add sound)."""
        self.move_forward()
        print("🗣️ Hello! I’m your Robo Desk Buddy!")


# --- Main loop ---
def main():
    bot = DeskBuddy()
    keyboard = bot.getKeyboard()
    keyboard.enable(TIME_STEP)

    while bot.step(TIME_STEP) != -1:
        key = keyboard.getKey()
        if key == ord('W'):   # press W for wave
            bot.wave()
        elif key == ord('B'): # press B for blink
            bot.blink_lights()
        elif key == ord('H'): # press H for hello
            bot.say_hello()
        elif key == ord('Y'):
            bot.say_hello(); bot.blink_lights(); bot.wave()

if __name__ == "__main__":
    main()
    print("Key pressed:", key)
