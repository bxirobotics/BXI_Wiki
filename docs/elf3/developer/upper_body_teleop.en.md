---
title: Upper-Body Teleoperation
---

# Upper-Body Teleoperation

This page is intended for customer-side deployment of ELF3 upper-body teleoperation. It focuses on Pico 4 Ultra setup, video streaming, simulation validation, real-robot startup, calibration, and operation. For node implementation, controller extension, and development details, refer to the example repository:

- Upper-body teleoperation example: [bxi_teleop_v2](https://github.com/konodoki/bxi_teleop_v2)
- ELF3 upper-body teleoperation Mod: [com.bxi.upper_body_teleop](https://github.com/konodoki/com.bxi.upper_body_teleop)

!!! warning "Safety"
    In the current example, the lower-body locomotion model does not directly output arm joint commands. Arm commands are generated from Pico controller poses through IK and then merged into the control pipeline. Real-robot operation may affect standing stability. Validate in simulation first, keep a safety operator nearby, and make sure the emergency stop is available.

## Function Overview

The upper-body teleoperation example includes:

- ELF3 reinforcement-learning motion-control example;
- Mujoco simulation and real-robot launch entries;
- Gamepad or keyboard remote control;
- Pico 4 Ultra video streaming;
- Pico controller pose to ELF3 dual-arm IK teleoperation;
- Optional teleoperation recording.

The included `BxiPicoApp-release.apk` has currently been tested on Pico 4 Ultra. The default deployment uses `elf3_arm_bringup_nohand.launch.py`, which does not start any external dexterous-hand driver.

## Environment

| Item | Requirement |
|---|---|
| Robot | ELF3 |
| OS | Ubuntu 22.04 |
| ROS version | ROS 2 Humble |
| Base packages | `/opt/bxi/bxi_ros2_pkg`, providing `communication`, `mujoco`, `hardware_elf3`, and related dependencies |
| Headset | Pico 4 Ultra |
| Camera | USB camera, default device `/dev/video4` |
| Video port | MediaMTX RTSP `2212` |
| Example repository | `bxi_teleop_v2` |

## Choose the ELF3 Project Directory

Use the project path that matches how the robot is started. Install the upper-body Mod in the independent `/opt/bxi/mods` directory rather than inside the App project; this directory is outside the App download and survives App updates.

!!! warning "Migrating an older project"
    Some older project versions already contain the upper-body Mod in the built-in project directory or `private_git_mods`. If that copy and `/opt/bxi/mods/com.bxi.upper_body_teleop` are both scanned, the runtime finds a duplicate Mod ID and refuses to start. Back up and move the old copy out of the scanned directories, keeping only `/opt/bxi/mods/com.bxi.upper_body_teleop`; do not leave two scannable copies.

| Startup method | Project directory | Build requirement |
|---|---|---|
| Robot remote controller | `~/bxi_ws/bxi_rl_controller_ros2_example` | Source tree; install the Mod in `/opt/bxi/mods` and rebuild after updating it. |
| App | `/opt/bxi/bxi_rl_controller_ros2_example` | App-downloaded prebuilt deployment; the Mod is loaded from `/opt/bxi/mods`, with no manual rebuild required. |

Clone the Mod into the independent `/opt/bxi/mods` directory.

## Quick Deployment

### 0. Clone the ELF3 Upper-Body Teleoperation Mod

The Mod is maintained in a separate repository and must be cloned manually before building the motion-control project:

```bash
sudo mkdir -p /opt/bxi/mods
sudo git clone https://github.com/konodoki/com.bxi.upper_body_teleop.git /opt/bxi/mods/com.bxi.upper_body_teleop
```

If it is already present, update it separately:

```bash
cd /opt/bxi/mods/com.bxi.upper_body_teleop
git pull --ff-only
```

The parent project does not track this directory. At runtime, the configured `/opt/bxi/mods` root is scanned recursively, so the Mod remains available after an App update.

### 1. Get The Example Project

Run the following on the robot controller or a ROS 2 host:

```bash
cd ~/bxi_ws
git clone https://github.com/konodoki/bxi_teleop_v2.git
cd bxi_teleop_v2
```

If GitHub is unavailable on site, download the repository in advance and copy it to `~/bxi_ws/bxi_teleop_v2`.

### 2. Install Dependencies

```bash
sudo apt update
sudo apt install -y \
  python3-colcon-common-extensions \
  ffmpeg \
  libglfw3-dev \
  libyaml-cpp-dev \
  python3-pip \
  python3-pyqt5

python3 -m pip install numpy scipy matplotlib ikpy onnx onnxruntime PyYAML
```

### 3. Build The Project

```bash
cd ~/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
bash build.sh
source install/setup.bash
```

!!! tip
    On the real robot, hardware-related commands should be run as root. Re-source ROS 2, the BXI base packages, and this project’s `install/setup.bash` in each root terminal.

## Pico Video Check

### 1. Prepare Pico And Camera

1. Install `BxiPicoApp-release.apk` from the repository root onto Pico 4 Ultra;
2. Make sure Pico and the computer running this project are on the same LAN;
3. Connect the camera to a USB 3.0 port;
4. The current code reads `/dev/video4` by default.

### 2. Start Pico Access And Video Streaming

```bash
cd ~/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

If the following log appears, the camera stream is being published:

```text
[pico_bxi_server-1] INF [RTSP] [session ...] is publishing to path 'video', 1 track (H264)
```

The Pico app scans devices on the LAN that expose port `2212` and lists possible RTSP server IPs. Select the corresponding IP with the Pico controller to view the stream. To close the stream view, press `A` on the right controller to enter passthrough mode.

You can also test streaming separately:

```bash
cd ~/bxi_ws/bxi_teleop_v2
bash push_rtsp.sh
```

## Simulation Validation

Validate in simulation before running on the real robot. Open 3 terminals and source the environment in each:

```bash
cd ~/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
```

Terminal 1: start the remote controller. Gamepad input is used by default:

```bash
ros2 launch remote_controller remote_controller.launch.py
```

Without a gamepad, use keyboard input:

```bash
ros2 launch remote_controller remote_controller_keyboard.launch.py
```

Terminal 2: start Pico, dual-arm IK, and video streaming:

```bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

Terminal 3: start Mujoco simulation and the control policy:

```bash
ros2 launch bxi_example_py_elf3 example_demo.launch.py
```

!!! warning
    `example_demo.launch.py` starts both simulation and the control program. After it starts, do not press the startup button on the controller again, otherwise the startup flow may be triggered repeatedly.

## Real-Robot Startup

Real-robot operation is higher risk. Before startup, confirm emergency stop, power, network, workspace, and surrounding safety.

Enter root first:

```bash
sudo su
cd /home/bxi/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
```

Open 3 root terminals.

Terminal 1: start the remote controller:

```bash
ros2 launch remote_controller remote_controller.launch.py
```

Terminal 2: start Pico, dual-arm IK, and video streaming:

```bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

Terminal 3: start the real-robot hardware node and control policy:

```bash
ros2 launch bxi_example_py_elf3 example_demo_hw.launch.py
```

If the launch reports that another hardware-control instance is already running, confirm and stop the old instance first. `example_demo_hw.launch.py` uses `/tmp/bxi_example_hw.lock` to avoid duplicate hardware-control startup.

## Calibration And Operation

1. After `elf3_arm_ikpy_control_pico` starts, raise both hands above the head;
2. When calibration starts, keep both arms as straight as possible and sweep a full spherical range around the shoulders;
3. Continue after the terminal reports successful calibration;
4. Use the remote controller to put the robot into the `normal` standing state;
5. Press `RT + A` to enter teleoperation mode;
6. Hold the Pico grip button. The corresponding robot arm starts following the Pico controller;
7. Press both triggers to start teleoperation recording. Release either trigger to stop recording.

Recording files are saved to:

```text
install/bxi_example_py_elf3/share/bxi_example_py_elf3/data/teleop_records
```

## Acceptance Check

After basic deployment, verify:

1. The Pico app can discover the video service IP on port `2212` and display the camera stream;
2. The `elf3_arm_bringup_nohand.launch.py` terminal continuously prints Pico connection or RTSP streaming logs;
3. The robot can enter standing and teleoperation flow in simulation;
4. When the Pico grip button is held, both arms follow the Pico controllers in simulation or on the real robot;
5. During real-robot operation, there are no continuous packet losses, protection triggers, or unexpected node exits.

## Troubleshooting

### `communication`, `mujoco`, Or `hardware_elf3` Not Found

The BXI ROS 2 base package environment is usually missing:

```bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
```

Then rebuild or restart.

### Pico Cannot Find The Video IP

Check:

1. Pico and the computer are on the same LAN;
2. The computer firewall is not blocking port `2212`;
3. MediaMTX is listening:

```bash
ss -lntup | grep 2212
```

### Camera Cannot Be Opened

The current code uses `/dev/video4` by default. If your camera uses another device number, modify:

```text
src/pico_bxi_server/src/pico_bxi_server.cpp
push_rtsp.sh
```

Also confirm that the camera is connected to a USB 3.0 port and the current user has camera access. For temporary debugging:

```bash
sudo chmod 777 /dev/video4
```

### `aero_hand_open` Not Found When Starting Full Bringup

The current repository does not include the `aero_hand_open` implementation. If no external dexterous-hand driver is installed, use:

```bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

### Real-Robot Nodes Cannot Discover Each Other

Make sure the robot and the terminal running the teleoperation project use the same `ROS_DOMAIN_ID`. Restart related ROS 2 nodes after changing it.

## Development Entry

Customer deployment usually does not require changes to the low-level video streaming, Pico data bridge, or IK node. To extend controller input, modify the state machine, replace the model, or connect a dexterous hand, refer to the repository README:

[https://github.com/konodoki/bxi_teleop_v2](https://github.com/konodoki/bxi_teleop_v2)
