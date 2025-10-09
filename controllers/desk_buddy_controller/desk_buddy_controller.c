#include <webots/robot.h>
#include <webots/motor.h>
#include <webots/keyboard.h>
#include <webots/led.h>
#include <webots/speaker.h>
#include <stdio.h>
#include <unistd.h>

// Time step in milliseconds
#define TIME_STEP 32

// Device pointers
WbDeviceTag left_wheel;
WbDeviceTag right_wheel;
WbDeviceTag head_motor;
WbDeviceTag led_left;
WbDeviceTag led_right;
WbDeviceTag speaker;

// Speed constants
#define MAX_SPEED 6.28
#define TURN_SPEED 3.0

void print_controls() {
  printf("================================\n");
  printf("DESKBUDDY ROBOT CONTROLS:\n");
  printf("  W = Wave (head tilt)\n");
  printf("  B = Blink LEDs\n");
  printf("  F = Move Forward\n");
  printf("  R = Move Backward\n");
  printf("  L = Turn Left\n");
  printf("  G = Turn Right\n");
  printf("  SPACE = Stop\n");
  printf("  Q = Quit\n");
  printf("================================\n");
}

void move_forward() {
  printf("➡️ Moving forward...\n");
  wb_motor_set_velocity(left_wheel, MAX_SPEED);
  wb_motor_set_velocity(right_wheel, MAX_SPEED);
}

void move_backward() {
  printf("⬅️ Moving backward...\n");
  wb_motor_set_velocity(left_wheel, -MAX_SPEED);
  wb_motor_set_velocity(right_wheel, -MAX_SPEED);
}

void turn_left() {
  printf("↪️ Turning left...\n");
  wb_motor_set_velocity(left_wheel, -TURN_SPEED);
  wb_motor_set_velocity(right_wheel, TURN_SPEED);
}

void turn_right() {
  printf("↩️ Turning right...\n");
  wb_motor_set_velocity(left_wheel, TURN_SPEED);
  wb_motor_set_velocity(right_wheel, -TURN_SPEED);
}

void stop_motors() {
  printf("⏹️ Stopping...\n");
  wb_motor_set_velocity(left_wheel, 0.0);
  wb_motor_set_velocity(right_wheel, 0.0);
}

void wave_head() {
  printf("👋 Waving...\n");
  
  // Right
  wb_motor_set_position(head_motor, 0.5);
  for (int i = 0; i < 15; i++)
    wb_robot_step(TIME_STEP);
  
  // Left
  wb_motor_set_position(head_motor, -0.5);
  for (int i = 0; i < 15; i++)
    wb_robot_step(TIME_STEP);
  
  // Center
  wb_motor_set_position(head_motor, 0.0);
  for (int i = 0; i < 15; i++)
    wb_robot_step(TIME_STEP);
  
  printf("👋 Wave complete!\n");
}

void blink_lights() {
  printf("✨ Blinking LEDs...\n");
  
  for (int blink = 0; blink < 3; blink++) {
    // ON
    wb_led_set(led_left, 1);
    wb_led_set(led_right, 1);
    for (int i = 0; i < 9; i++)  // 0.3 seconds
      wb_robot_step(TIME_STEP);
    
    // OFF
    wb_led_set(led_left, 0);
    wb_led_set(led_right, 0);
    for (int i = 0; i < 9; i++)  // 0.3 seconds
      wb_robot_step(TIME_STEP);
  }
  
  printf("✨ Blink complete!\n");
}

int main() {
  wb_robot_init();
  
  // Initialize devices
  left_wheel = wb_robot_get_device("left_wheel_motor");
  right_wheel = wb_robot_get_device("right_wheel_motor");
  head_motor = wb_robot_get_device("tilt_motor");
  led_left = wb_robot_get_device("eye_led_left");
  led_right = wb_robot_get_device("eye_led_right");
  speaker = wb_robot_get_device("speaker");
  
  // Set motors to velocity control mode
  wb_motor_set_position(left_wheel, INFINITY);
  wb_motor_set_position(right_wheel, INFINITY);
  wb_motor_set_velocity(left_wheel, 0.0);
  wb_motor_set_velocity(right_wheel, 0.0);
  
  // Set head motor to position control
  wb_motor_set_velocity(head_motor, 1.0);
  
  // Initialize keyboard
  wb_keyboard_enable(TIME_STEP);
  
  printf("🤖 Robo Desk Buddy is alive!-c\n");
  print_controls();
  
  // Main loop
  while (wb_robot_step(TIME_STEP) != -1) {
    int key = wb_keyboard_get_key();
    
    if (key == 'W' || key == 'w') {
      wave_head();
    } 
    else if (key == 'B' || key == 'b') {
      blink_lights();
    }
    else if (key == 'F' || key == 'f') {
      move_forward();
    }
    else if (key == 'R' || key == 'r') {
      move_backward();
    }
    else if (key == 'L' || key == 'l') {
      turn_left();
    }
    else if (key == 'G' || key == 'g') {
      turn_right();
    }
    else if (key == ' ') {
      stop_motors();
    }
    else if (key == 'Q' || key == 'q') {
      printf("🛑 Shutting down...\n");
      break;
    }
  }
  
  wb_robot_cleanup();
  return 0;
}