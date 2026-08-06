# Minimal 31-DoF ELF3 Control

This guide presents two joint-control paths. To control only the head, publish named joint commands directly to `actuators_cmds_override` without writing code. For complete 31-DoF control, create a Mod containing only `state.py` and `mod.yaml` and generate the trajectory directly in `on_update()`.

The example targets Mod API 4.0:

- [Complete framework source](https://github.com/bxirobotics/bxi_rl_controller_ros2_example.git)
- [Complete Mod API documentation](https://github.com/bxirobotics/bxi_rl_controller_ros2_example/wiki)

Run the commands below from the framework repository root.

## Before you start: hardware defaults to 29 DoF

The hardware launch uses `enable_head:=auto` by default and reads the robot module configuration from `/opt/bxi/robot_config.yaml`. Both of the following conditions must be satisfied before the two head joints and the complete 31-DoF hardware are enabled:

1. `/opt/bxi/robot_config.yaml` exists and can be read successfully;
2. the configuration contains `modules.head.enabled: true`.

The minimum configuration structure is shown below. Production configuration should be generated with `bxi_robot_config_tool`:

```yaml
modules:
  head:
    enabled: true
```

Any of the following cases falls back to the built-in 29-DoF configuration without the head motors:

- `/opt/bxi/robot_config.yaml` is missing, unreadable, or malformed;
- `modules.head.enabled` is absent;
- `modules.head.enabled` is `false`.

The startup log reports the selected mode:

```text
# 31 DoF
[bxi hardware config] package=hardware_elf3_head, ...

# Default 29 DoF
[bxi hardware config] package=hardware_elf3, ...
```

In 29-DoF mode, the runtime joint layout does not contain `head_z_joint` or `head_y_joint`, so the head-override command below is rejected as containing unknown joint names. Generate a valid `/opt/bxi/robot_config.yaml` and restart the hardware program first. The simulation ELF3 model already contains both head joints and is not controlled by this hardware configuration.

!!! note "Manual overrides are for debugging"
    The hardware launch also accepts `enable_head:=true` or `enable_head:=false` to override automatic detection. Standard deployments should use `/opt/bxi/robot_config.yaml` so the software configuration cannot silently disagree with the physical hardware.

!!! danger "Validate in simulation and choose the correct test setup"
    Both joint overrides and custom Mods produce motor commands directly. Before testing on hardware, clear all people and obstacles, keep the emergency stop ready, and validate joint directions with small angles and low gains.

    When the robot is standing on the ground, arm or hand overrides require a model that does not rely on the arms for balance, such as `com.bxi.basic_actions/hello` or `com.bxi.basic_actions/applause`. The alternative is to suspend the robot securely. During a suspended `actuators_cmds_override` test, the underlying state may be only zero-position mode (`initial_pos`) or PD mode (`pd_brake`); do not enter walking, hello, applause, dance, or any other mode.

## 1. No-code head-joint override

At the final output stage, the controller reads override commands of type `communication/msg/ActuatorCmds` and replaces only the joints listed in `actuators_name`. All other joints remain controlled by the current state or policy, so head-only control does not require a Mod or a complete 31-element command.

!!! warning "Prepare the underlying model before overriding an arm or hand"
    `actuators_cmds_override` replaces only the selected joints; it cannot make the original balance model adapt automatically to a new arm motion. With the robot standing on the ground, enter the arm-independent `hello` or `applause` state before publishing arm or hand overrides. When the robot is suspended, do not enter those actions; remain in `initial_pos` or `pd_brake` only.

The override topic includes the launch-time `topic_prefix`:

| Environment | Topic |
| --- | --- |
| Simulation | `/simulation/actuators_cmds_override` |
| Hardware | `/hardware/actuators_cmds_override` |

Overrides are disabled in zero-torque mode by default. After starting the robot and waiting for the joint layout to initialize, enter zero-position mode or another actively controlled state. For example, enter zero-position mode with:

```bash
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 1}"

ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 0}"
```

!!! warning "Reset every button event to 0"
    `MotionCommands` button events use rising-edge detection, and the program retains the last value received for each event. After manually publishing any nonzero button value over ROS, publish `0` to the same button slot to return it to the released state. Otherwise, the next action using that button slot may not produce a new rising edge.

The command below overrides both head joints at 20 Hz. The targets for `head_z_joint` and `head_y_joint` are `0.20 rad` and `-0.10 rad`, respectively:

```bash
# Simulation
ros2 topic pub -r 20 \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds \
  '{
    actuators_name: ["head_z_joint", "head_y_joint"],
    pos: [0.20, -0.10],
    kp: [16.747, 16.747],
    kd: [1.066, 1.066]
  }'
```

Use the same message on hardware and change only the topic:

```bash
# Hardware; suspend the robot and prepare the emergency stop first
ros2 topic pub -r 20 \
  /hardware/actuators_cmds_override \
  communication/msg/ActuatorCmds \
  '{
    actuators_name: ["head_z_joint", "head_y_joint"],
    pos: [0.20, -0.10],
    kp: [16.747, 16.747],
    kd: [1.066, 1.066]
  }'
```

`actuators_name` defines the joint order for every command array. The lengths of `pos`, `kp`, and `kd` must match the number of joint names. Omitted `vel` and `torque` fields are treated as zero.

The default override timeout is `0.2 s`, so `--once` cannot hold a target. After the 20 Hz publisher stops, the command expires automatically and blends back to the current state's output over `0.2 s`. An empty message explicitly requests release:

```bash
# Simulation; replace simulation with hardware on the robot
ros2 topic pub --once \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds '{}'
```

To generate a time-varying head trajectory, continuously publish the same message type from a ROS node; each new message atomically replaces the previous override. Use the Mod approach below when state-machine integration, a whole-body trajectory, or more complex control logic is required.

## 2. The 31-joint order

The `qpos`, `kp`, and `kd` arrays in a `MotorFrame` must use the same joint layout. The formula arrays in this example use the order below; position values are in radians.

| Index | Joint | Index | Joint |
| ---: | --- | ---: | --- |
| 0 | `waist_y_joint` | 16 | `l_shoulder_x_joint` |
| 1 | `waist_x_joint` | 17 | `l_shoulder_z_joint` |
| 2 | `waist_z_joint` | 18 | `l_elbow_y_joint` |
| 3 | `l_hip_y_joint` | 19 | `l_wrist_x_joint` |
| 4 | `l_hip_x_joint` | 20 | `l_wrist_y_joint` |
| 5 | `l_hip_z_joint` | 21 | `l_wrist_z_joint` |
| 6 | `l_knee_y_joint` | 22 | `r_shoulder_y_joint` |
| 7 | `l_ankle_y_joint` | 23 | `r_shoulder_x_joint` |
| 8 | `l_ankle_x_joint` | 24 | `r_shoulder_z_joint` |
| 9 | `r_hip_y_joint` | 25 | `r_elbow_y_joint` |
| 10 | `r_hip_x_joint` | 26 | `r_wrist_x_joint` |
| 11 | `r_hip_z_joint` | 27 | `r_wrist_y_joint` |
| 12 | `r_knee_y_joint` | 28 | `r_wrist_z_joint` |
| 13 | `r_ankle_y_joint` | 29 | `head_z_joint` |
| 14 | `r_ankle_x_joint` | 30 | `head_y_joint` |
| 15 | `l_shoulder_y_joint` |  |  |

The example explicitly binds this layout to its `MotorFrame`. The runtime layout may use a different order as long as it contains the same 31 named joints; the framework maps commands to the actual order by joint name.

## 3. Create the Mod

!!! danger "This Mod has no balance capability"
    The example `on_update()` produces only joint positions and gains. It does not use the IMU, foot contacts, or a balance policy, and it provides no standing stabilization, disturbance rejection, or fall protection. It can only move joints according to the hard-coded formulas; it cannot keep the robot standing.

    To avoid mixing an unbalanced state with the rule that a suspended robot must remain in zero-position or PD mode, this tutorial runs the formula Mod in simulation only. To verify joint motion on hardware, use `actuators_cmds_override` from the previous section, suspend the robot, and keep the underlying state in `initial_pos` or `pd_brake` throughout the test.

```bash
cd ~/bxi_ws/bxi_rl_controller_ros2_example
mkdir -p src/bxi_example_py_elf3/mods/com.example.elf3_31dof
```

Only two files are required:

```text
src/bxi_example_py_elf3/mods/com.example.elf3_31dof/
├── mod.yaml
└── state.py
```

## 4. Write `state.py`

```python
import math

import numpy as np

from bxi_example_py_elf3.framework.mod_api import JointLayout, RobotControlState


ELF3_JOINT_NAMES = (
    "waist_y_joint", "waist_x_joint", "waist_z_joint",
    "l_hip_y_joint", "l_hip_x_joint", "l_hip_z_joint",
    "l_knee_y_joint", "l_ankle_y_joint", "l_ankle_x_joint",
    "r_hip_y_joint", "r_hip_x_joint", "r_hip_z_joint",
    "r_knee_y_joint", "r_ankle_y_joint", "r_ankle_x_joint",
    "l_shoulder_y_joint", "l_shoulder_x_joint", "l_shoulder_z_joint",
    "l_elbow_y_joint", "l_wrist_x_joint", "l_wrist_y_joint",
    "l_wrist_z_joint", "r_shoulder_y_joint", "r_shoulder_x_joint",
    "r_shoulder_z_joint", "r_elbow_y_joint", "r_wrist_x_joint",
    "r_wrist_y_joint", "r_wrist_z_joint", "head_z_joint",
    "head_y_joint",
)
ELF3_LAYOUT = JointLayout(ELF3_JOINT_NAMES, label="ELF3 31-DoF")


class Elf31DofState(RobotControlState):
    # The order exactly matches ELF3_JOINT_NAMES. The first 29 entries use
    # zero-position-mode gains; the final two entries are the head gains.
    KP = np.array([
        500, 500, 300,
        300, 100, 100, 300, 50, 50,
        300, 100, 100, 300, 50, 50,
        100, 80, 80, 100, 20, 20, 20,
        100, 80, 80, 100, 20, 20, 20,
        16.747, 16.747,
    ], dtype=np.float32)
    KD = np.array([
        3, 3, 3,
        2.5, 2, 2, 2.5, 2, 2,
        2.5, 2, 2, 2.5, 2, 2,
        2.5, 2, 2, 2.5, 1, 1, 1,
        2.5, 2, 2, 2.5, 1, 1, 1,
        1.066, 1.066,
    ], dtype=np.float32)

    def __init__(self, name, state_id):
        super().__init__(name, state_id)
        self.elapsed = 0.0
        self.qpos = np.zeros(31, dtype=np.float32)

    def on_enter(self, ctx):
        if frozenset(ctx.robot_layout.names) != frozenset(ELF3_JOINT_NAMES):
            raise RuntimeError(
                "ELF3 joint set mismatch: "
                f"expected={ELF3_JOINT_NAMES}, actual={ctx.robot_layout.names}"
            )
        self.elapsed = 0.0

    def on_update(self, ctx, dt):
        # Regenerate the target from zero every cycle; do not accumulate offsets.
        self.qpos.fill(0.0)
        phase = 2.0 * math.pi * 0.25 * self.elapsed

        # Hard-coded 31-DoF example: hold the waist and legs at zero while
        # moving both arms and the head through small sinusoidal trajectories.
        self.qpos[15] = 0.15 * math.sin(phase)        # left shoulder y
        self.qpos[18] = 0.12 * math.sin(phase)        # left elbow y
        self.qpos[22] = -0.15 * math.sin(phase)       # right shoulder y
        self.qpos[25] = -0.12 * math.sin(phase)       # right elbow y
        self.qpos[29] = 0.10 * math.sin(phase)        # head z
        self.qpos[30] = 0.06 * math.sin(2.0 * phase)  # head y

        frame = self._motor_frame(
            ctx, self.qpos, self.KP, self.KD, layout=ELF3_LAYOUT
        )
        self._apply_frame(ctx, frame)
        self.elapsed += dt
```

There are four essential points:

1. `qpos`, `KP`, and `KD` are all 31-element `float32` arrays interpreted using `ELF3_LAYOUT`, so the state commands the complete robot layout every cycle.
2. `phase` advances using the framework-provided `dt`, rather than assuming an exact number of loop iterations.
3. `_motor_frame()` reuses the state's internal `MotorFrame` buffer, and `_apply_frame()` submits it to the framework.
4. Neither `EntryFrameProvider` nor `RunningFrameProvider` is implemented; the trajectory is produced exclusively by `on_update()`.

The current `MotorFrame` also supports the MIT `vel` and `torque` fields. This example omits both when calling `_motor_frame()`, so the framework explicitly fills them with zero.

Only six joints move in this formula, but the other 25 joints are still actively controlled by `qpos=0` and their corresponding `kp/kd`. To change the motion, edit the formulas for the relevant indices in `on_update()` without changing the array order.

## 5. Write `mod.yaml`

```yaml
schema: 1
id: com.example.elf3_31dof
name: ELF3 31-DoF Formula Trajectory
version: 1.0.0
api: ">=4,<5"
enable: true
entrypoint: null
visibility: public
requires:
  - id: com.bxi.basic_actions
    version: ">=1,<2"
conflicts: []
python_exports: []
runtime_requirements:
  python: []
  ros: []
  system: []

events:
  activate:
    slot: btn_10
    value: 99

states:
  formula_31dof:
    factory: state:Elf31DofState
    label: 31-DoF Formula Trajectory
    priority: 100
    group: Customer
    icon: waves
    confirm: true
    confirm_message: This unbalanced example is for simulation only

routes:
  - from: com.bxi.basic_actions/initial_pos
    event: activate
    to: formula_31dof

  - from: formula_31dof
    event: com.bxi.basic_actions/initial_pos
    to: com.bxi.basic_actions/initial_pos
```

Both routes intentionally omit `transition`. The project's `elf3_state_machine.yaml` sets `default_transition` to `instant`, so the state changes immediately and the target state's `on_update()` starts on the next control cycle. This is what “no transition” means in this example. If the system default has been changed, add `transition: instant` explicitly to both routes.

The example can only be entered from `com.bxi.basic_actions/initial_pos` (zero-position mode). This both reduces the target discontinuity during an instant switch and reflects the fact that the formula trajectory has no balance capability. Do not add routes from `normal`, walking, or other action states. Send `btn_10=99` to enter and use the zero-position-mode command to return. This example does not use `btn_10=10` because that binding is already owned by `com.bxi.any_motion/activate`.

## 6. Build and run

```bash
colcon build --packages-select bxi_example_py_elf3 \
  --symlink-install --merge-install
source install/setup.bash
```

Start in simulation:

```bash
ros2 launch bxi_example_py_elf3 example_demo.launch.py
```

First send the zero-position-mode command:

```bash
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 1}"

ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 0}"
```

After the robot enters zero-position mode, send `btn_10=99` to enter the formula-trajectory state:

```bash
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_10: 99}"

# Releasing btn_10 is required so later btn_10 actions can trigger
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_10: 0}"
```

Publishing `btn_10=0` only restores the released button state; it does not exit the formula-trajectory state that was just entered.

A successful load includes this log entry:

```text
[com.example.elf3_31dof]: loaded v1.0.0: .../com.example.elf3_31dof
```

The fully qualified state name is `com.example.elf3_31dof/formula_31dof`.

The formula-trajectory Mod in this tutorial is for simulation only and must not be treated as a hardware standing controller. To verify joint motion on hardware, use `actuators_cmds_override`; after suspension, keep the underlying state in `initial_pos` or `pd_brake` only. Hardware control requires root privileges. Stop the background autostart service first so two controllers cannot command the motors concurrently. See the [Motion Control Development Guide](motioncontrol.md#launching-the-robot-program) for startup instructions.

## Troubleshooting

### Joint layout mismatch

Inspect the actual `ctx.robot_layout.names`. A different order does not affect control because the framework maps the names from `ELF3_LAYOUT` automatically. Update the layout and all three 31-element arrays only when joints are missing or the hardware uses different joint names.

### The state loads but the robot does not move

Make sure the latest workspace has been loaded with `source install/setup.bash`, and confirm that the startup log contains `com.example.elf3_31dof`. A non-symlink installation must be rebuilt after every Mod change.

### The robot jumps when switching

This is an expected risk of an instant switch. Enter zero-position mode first, and ensure that `on_update()` produces the zero pose at `elapsed=0`. If the state must enter smoothly from arbitrary poses, use a Transition; that is outside this minimal example.
