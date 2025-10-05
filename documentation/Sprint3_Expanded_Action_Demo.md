# Robo Desk Buddy - Sprint 3 Documentation

## Sprint 3 (Expanded Robot Action Demo)

### Sprint 3 Deliverables:
- ✅ Controller extended with additional placeholder action (turn + speak)
- ✅ Robot can switch between actions during simulation
- ✅ Documentation of how multiple actions were wired together

### Unit Tests:
- Robot executes second action without errors
- Robot can switch between first and second action during a single run

### To-Dos:
- [x] Add second placeholder action (turn + speak)
- [x] Update controller to handle multiple actions
- [x] Run and verify both actions in sequence
- [x] Document process

---

## Expanded Action Implementation

### New Actions Added

#### Turn Action (Placeholder for Movement)
```python
def turn(self, direction, duration):
    """
    Thread-safe turn action - rotates robot left or right
    
    Parameters:
    - direction: 'left' or 'right'
    - duration: time in seconds to turn
    
    Note: This is a placeholder for actual movement.
    In a real implementation, this would control wheel motors.
    """
    print(f"🔄 Turning {direction} for {duration} seconds...")
    
    # Simulate turning action
    time.sleep(duration)  # Wait for the duration of the turn
    
    print(f"🔄 Turn {direction} complete!")
```

**Key Features:**
- **Parameterized action**: Takes direction ('left'/'right') and duration
- **Placeholder implementation**: Uses `time.sleep()` to simulate actual movement
- **Future-ready**: Documentation shows how to extend for real motor control
- **Thread-safe**: Can be used with threading system

#### Speak Action (Placeholder for Speech)
```python
def speak(self, message):
    """
    Thread-safe speak action - prints a message
    
    Parameters:
    - message: The string message to "speak"
    
    Note: This is a placeholder for actual speech synthesis.
    """
    print(f"🗣️ Speaking: {message}")
    time.sleep(1.0)  # Simulate time taken to speak
    print("🗣️ Speak action complete!")
```

**Key Features:**
- **Message-based**: Takes any string message as parameter
- **Simulation timing**: 1-second delay simulates speech synthesis time
- **Extensible**: Ready for integration with text-to-speech libraries
- **Clear feedback**: Shows start and completion of speech action

---

## Action Integration System

### Original Actions (Sprint 1-2)
```python
def wave(self):          # Head tilt left/right
def blink_lights(self):  # LED flashing  
def say_hello(self):     # Greeting messages
```

### New Actions (Sprint 3)
```python
def turn(self, direction, duration):  # Robot rotation simulation
def speak(self, message):             # Speech synthesis simulation
```

### Combined Action Demonstrations

#### Turn + Speak Combination
```python
# Example usage in keyboard controls:
elif key == ord('T'):  # Turn action
    bot.run_async(lambda: bot.turn('left', 2.0))
    
elif key == ord('M'):  # Speak action  
    bot.run_async(lambda: bot.speak("Hello, I am turning left!"))
    
elif key == ord('C'):  # Combined turn + speak
    def combined_action():
        bot.speak("I'm about to turn left")
        bot.turn('left', 3.0)
        bot.speak("Turn complete!")
    
    bot.run_async(combined_action)
```

---

## Action Switching During Simulation

### Sequential Action Switching
The robot can now switch between **5 different actions** during a single simulation run:

1. **Wave** (`W` key) - Head tilting motion
2. **Blink** (`B` key) - LED eye flashing  
3. **Hello** (`H` key) - Greeting sequence
4. **Turn** (`T` key) - Rotation movement simulation
5. **Speak** (`M` key) - Voice message simulation

### Action Switch Implementation
```python
while bot.step(TIME_STEP) != -1:  # During simulation
    key = keyboard.getKey()
    
    # Original actions
    if key == ord('W'):
        bot.run_async(bot.wave)
    elif key == ord('B'):
        bot.run_async(bot.blink_lights)
    elif key == ord('H'):
        bot.run_async(bot.say_hello)
    
    # NEW Sprint 3 actions
    elif key == ord('T'):  # Turn action
        bot.run_async(lambda: bot.turn('left', 2.0))
    elif key == ord('M'):  # Speak action
        bot.run_async(lambda: bot.speak("Hello from DeskBuddy!"))
    
    # Combined demonstrations
    elif key == ord('Y'):  # All actions simultaneously
        bot.run_async(bot.wave)
        bot.run_async(bot.blink_lights)
        bot.run_async(lambda: bot.turn('right', 1.5))
        bot.run_async(lambda: bot.speak("Multiple actions running!"))
```

**Key Benefits:**
- **Real-time switching**: Change actions without stopping simulation
- **No conflicts**: Threading system prevents action interference  
- **Immediate response**: Actions start instantly when keys are pressed
- **Overlapping capability**: Multiple actions can run simultaneously

---

## Multiple Action Coordination

### How Actions are Wired Together

#### 1. Threading Foundation
```python
# Threading system allows multiple actions to run simultaneously
self.action_lock = threading.Lock()  # Prevents device conflicts
self.active_threads = []             # Track running actions

def run_async(self, func):
    # Execute any action in separate thread
    # Automatic cleanup when action completes
```

#### 2. Action Parameters and Flexibility
```python
# Actions can now take parameters for customization
bot.turn('left', 3.0)      # Turn left for 3 seconds
bot.turn('right', 1.5)     # Turn right for 1.5 seconds
bot.speak("Custom message") # Speak any message
```

#### 3. Action Composition
```python
def patrol_sequence():
    """Example of combining multiple actions"""
    bot.speak("Starting patrol")
    bot.turn('left', 2.0)
    bot.speak("Scanning left area")
    bot.turn('right', 4.0)  
    bot.speak("Scanning right area")
    bot.turn('left', 2.0)   # Return to center
    bot.speak("Patrol complete")

# Execute complex sequence
bot.run_async(patrol_sequence)
```

---

## Enhanced Control System

### Updated Keyboard Controls

#### Individual Actions
- **W** = Wave (head tilt)
- **B** = Blink LEDs
- **H** = Say Hello  
- **T** = Turn Left (2 seconds) 🆕
- **M** = Speak Message 🆕

#### Combined Demonstrations  
- **C** = Combined Turn + Speak sequence 🆕
- **Y** = All actions simultaneously
- **S** = Stop all actions
- **Q** = Quit simulation

#### Advanced Combinations
```python
# Sprint 3 enhanced controls
elif key == ord('C'):  # Combined turn + speak
    def combined_demo():
        bot.speak("Preparing to demonstrate turning")
        time.sleep(0.5)  # Brief pause
        bot.turn('left', 2.0)
        bot.speak("Turn demonstration complete")
    
    print("🔄 Starting combined turn + speak demo...")
    bot.run_async(combined_demo)

elif key == ord('1'):  # Quick left turn
    bot.run_async(lambda: bot.turn('left', 1.0))
    
elif key == ord('2'):  # Quick right turn  
    bot.run_async(lambda: bot.turn('right', 1.0))

elif key == ord('3'):  # Custom greeting
    bot.run_async(lambda: bot.speak("Greetings! I'm your desk companion."))
```

---

## Testing and Verification

### Sprint 3 Testing Procedures

#### Test 1: Second Action Execution
1. **Start simulation** and press **T** (Turn)
2. **Verify**: Console shows "🔄 Turning left for 2.0 seconds..."
3. **Wait**: Action completes after 2 seconds  
4. **Verify**: Console shows "🔄 Turn left complete!"
5. **Result**: ✅ Second action executes without errors

#### Test 2: Action Switching During Simulation
1. **Press W** (Wave) - action starts
2. **Immediately press T** (Turn) - second action starts
3. **Verify**: Both actions run simultaneously
4. **Press M** (Speak) while others are running
5. **Verify**: All three actions execute concurrently
6. **Result**: ✅ Robot switches between actions during single run

#### Test 3: Parameter Flexibility  
1. **Test different turn durations**: Modify `turn('left', X)` with different X values
2. **Test different messages**: Modify `speak("message")` with different strings
3. **Verify**: Actions adapt to different parameters correctly
4. **Result**: ✅ Actions are flexible and parameterized

#### Test 4: Combined Action Sequences
1. **Press C** (Combined demo) 
2. **Verify**: Speaks first, then turns, then speaks again in sequence
3. **Verify**: Actions flow smoothly from one to the next
4. **Result**: ✅ Multiple actions can be wired together in sequences

---

## Documentation: How Actions Are Wired Together

### 1. **Action Definition Layer**
```python
# Each action is defined as an independent method
def turn(self, direction, duration):     # Parameterized actions
def speak(self, message):                # Message-based actions  
def wave(self):                          # Simple actions
```

### 2. **Threading Execution Layer**
```python
# Actions are executed via threading system
bot.run_async(bot.wave)                  # Simple execution
bot.run_async(lambda: bot.turn('left', 2.0))  # Parameterized execution
```

### 3. **Keyboard Input Layer**
```python
# User input triggers action execution
elif key == ord('T'):
    bot.run_async(lambda: bot.turn('left', 2.0))
```

### 4. **Action Composition Layer**  
```python
# Multiple actions combined into complex sequences
def complex_behavior():
    bot.speak("Starting complex behavior")
    bot.turn('left', 1.0)
    bot.wave()
    bot.turn('right', 2.0)
    bot.speak("Behavior complete")

bot.run_async(complex_behavior)
```

### 5. **Thread Management Layer**
```python
# System tracks and manages all running actions
self.active_threads = []     # Track running threads
self.action_lock = Lock()    # Prevent device conflicts
```

**This layered architecture allows:**
- ✅ **Independent actions** that can run alone
- ✅ **Simultaneous execution** of multiple actions
- ✅ **Dynamic composition** of complex behaviors  
- ✅ **Real-time switching** between different actions
- ✅ **Parameter customization** for flexible behaviors

---

## Sprint 3 Achievements

### Core Requirements Met ✅

#### 1. Controller Extended with Additional Actions
- **Turn action**: Parameterized robot rotation simulation
- **Speak action**: Message-based speech synthesis simulation  
- **Both actions**: Fully integrated with existing threading system

#### 2. Action Switching During Simulation
- **5 total actions** available: Wave, Blink, Hello, Turn, Speak
- **Real-time switching**: Change actions without stopping simulation
- **Immediate response**: Actions execute instantly when triggered
- **No conflicts**: Multiple actions can overlap safely

#### 3. Multiple Action Wiring Documentation
- **Layered architecture**: Clear separation of concerns
- **Threading integration**: How actions work with thread system
- **Parameter support**: How to customize action behaviors
- **Composition patterns**: How to combine actions into sequences

### Enhanced Features Beyond Requirements ✨

#### Advanced Action Coordination
- **Parameterized actions**: `turn(direction, duration)` and `speak(message)`
- **Action composition**: Ability to create complex multi-action sequences
- **Flexible execution**: Lambda functions for custom parameter passing
- **Thread-safe coordination**: All actions work seamlessly together

#### Improved User Experience
- **Enhanced keyboard controls**: More intuitive key mappings
- **Clear action feedback**: Console messages show action progress  
- **Flexible demonstrations**: Multiple ways to trigger action combinations
- **Emergency controls**: Stop and quit functionality maintained

---

## Files Modified in Sprint 3

### Controller Updates
- `controllers/desk_buddy_controller/desk_buddy_controller.py`
  - Added `turn(direction, duration)` method
  - Added `speak(message)` method  
  - Enhanced keyboard controls with T and M keys
  - Added combined action demonstrations
  - Updated simultaneous action demo to include new actions

### Key Code Additions
- **Parameterized Actions**: Methods that accept custom parameters
- **Action Composition**: Ability to combine multiple actions in sequences
- **Enhanced Controls**: More keyboard options for triggering actions
- **Flexible Execution**: Lambda function integration for parameter passing

---

## Sprint Progression

**Sprint 1 Status**: ✅ Complete (Setup + Repo + Scaffolding)  
**Sprint 2 Status**: ✅ Complete (Manual Trigger Actions)  
**Sprint 3 Status**: ✅ Complete (Expanded Action Demo - Turn + Speak)  
**Next Sprint**: Sprint 4 - Advanced Threading Implementation

---

## Usage Examples

### Basic Action Usage
```python
# Individual actions
press 'W'  → Wave head
press 'B'  → Blink LEDs  
press 'H'  → Say hello
press 'T'  → Turn left 2 seconds
press 'M'  → Speak "Hello from DeskBuddy!"

# Combined actions
press 'C'  → Turn + speak sequence
press 'Y'  → All actions simultaneously  
```

### Custom Action Development
```python
# Template for new parameterized actions
def my_custom_action(self, param1, param2):
    print(f"🤖 Starting custom action with {param1} and {param2}")
    time.sleep(param2)  # Simulate action duration
    print("🤖 Custom action complete!")

# Integration with keyboard
elif key == ord('X'):
    bot.run_async(lambda: bot.my_custom_action("test", 1.5))
```

This Sprint 3 implementation establishes the foundation for complex robot behaviors by demonstrating how multiple parameterized actions can be seamlessly integrated, executed simultaneously, and combined into sophisticated behavioral sequences.