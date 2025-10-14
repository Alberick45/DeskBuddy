# 🤖 RoboDeskBuddy

A playful desktop companion robot built in **Webots**. This repo tracks development sprints, setup, and experiments with controllers and devices.

---

## 📦 Requirements

Before you begin, make sure you have the following installed:

* [Webots](https://cyberbotics.com/) (latest stable release)
* Python 3.9+
* Git (for cloning and version control)
* VS Code (recommended for editing controllers & world files)

---

## 🚀 Project Setup

1. **Clone the repo**

   ```bash
   git clone <your-repo-url>
   cd RoboDeskBuddy
   ```

2. **Create Webots project directory**

   * Open Webots → `File` → `New Project Directory`
   * Select this repo folder
   * Give your world a name (e.g., `robo_desk_buddy_world.wbt`)
   * Click **Finish**

3. **Controller setup**

   * In `/controllers/`, create a folder named `robo_desk_buddy/`
   * Inside it, create `robo_desk_buddy.py`
   * Example skeleton:

     ```python
     from controller import Robot

     def run_robot():
         robot = Robot()
         timestep = int(robot.getBasicTimeStep())

         while robot.step(timestep) != -1:
             print("Hello from RoboDeskBuddy!")

     if __name__ == "__main__":
         run_robot()
     ```

4. **Running simulation**

   * Open your world in Webots
   * Press **Play** ▶️
   * Controller logs will appear in the console

---

## 🎥 World File Basics

* You can alter the **viewpoint** (camera position) using:

  * **Mouse scroll**: zoom in/out
  * **Hold + drag**: tilt / pan the scene
  * **Ctrl + Shift + R**: reload view
* Save when prompted to keep the new orientation.

Viewpoint editing can also be done in **VS Code** by adjusting the `Viewpoint` node values (translation, orientation).

---

## 🏗️ Sprint Log

### Week 1 – Robot Dev

**Sprint: Setup + Repo + Project Saving**

* ✅ Git repo created for project code
* ✅ Webots installed and running
* ✅ Minimal world file created with robot loaded
* ✅ Basic controller created (placeholder logging action)
* ✅ Setup steps documented

**Unit Test:**

* World opens in Webots without errors

**To-Dos:**

* [ ] Polish repo README
* [ ] Expand basic controller

---

### Sprint 2 – Placeholder Robot Action

* ✅ Controller updated to include at least one placeholder action (e.g., wave, move forward, blink LED)
* ✅ Logging added for verification

**Unit Test:**

* 1 placeholder action executes without errors

**To-Dos:**

* [ ] Add more placeholder actions
* [ ] Verify controller logs

---

### Sprint 3 – Expanded Robot Action Demo

* ✅ Controller extended with second placeholder action (e.g., turn + speak)
* ✅ Robot can switch between actions during simulation
* ✅ Documented how actions are wired in controller

**Unit Test:**

* Robot executes second action without errors
* Robot switches between actions in one run

**To-Dos:**

* [ ] Add third action for variety
* [ ] Sequence multiple actions together

---

## 🔮 Long-Term Vision

* Add **LED eyes** with glow effect
* Experiment with **motors** for waving or nodding
* Create **voice or sound placeholders**
* Develop action sequences (dance, greet, idle animations)

---

## 📝 Notes

* Devices must be declared in the **world file** before you can use them in the controller.
* Use `robot.getDevice("device_name")` in Python to access motors, LEDs, sensors, etc.
* Save + reload the world after making edits.

Shape {
      appearance PBRAppearance {
        baseColor 0.2 0.6 0.9
        roughness 0.3
        metalness 0.1
      }
      geometry Box {
        size 0.25 0.3 0.25
      }
    }

CadShape {
        url "models/baymax_body.obj"
      } within children within endpoint solid