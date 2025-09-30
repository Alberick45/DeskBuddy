from controller import Robot

# Time step
TIME_STEP = 32

# Initialize robot
robot = Robot()
print("🤖 Robo Desk Buddy is alive!")

# Get devices
led = robot.getDevice("eye_led")
motor = robot.getDevice("tilt_motor")

# --- Actions ---

def move_forward():
    print("moving forward")
def move_backward():
    print("moving back")
def move_left():
    print("moving left")
def move_right():
    print("moving right")    
    
def wave(step_count):
    """Make the robot tilt as a wave gesture."""
    angle = (step_count % 40) - 20  # oscillates between -20 and 20
    print(f"👋 Waving at angle {angle}")
    motor.setPosition(angle)

def blink_lights(step_count):
    """Blink LED on and off."""
    if (step_count // 10) % 2 == 0:
        led.set(1)  # on
        print(f" led on")
    else:
        led.set(0)  # off
        print(f" led off")

def say_hello():
    """Print a hello message (later could add sound)."""
    print("🗣️ Hello! I’m your Robo Desk Buddy!")

# --- Main loop ---

step_count = 0
while robot.step(TIME_STEP) != -1:
    step_count += 1

    # Call actions
    if step_count % 200 < 100:
        wave(step_count)
    blink_lights(step_count)

    if step_count % 300 == 0:
        say_hello()
