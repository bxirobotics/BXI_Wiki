---
title: Upper-Body Teleoperation
---

# Upper-Body Teleoperation

`com.bxi.upper_body_teleop` is a standalone ELF3 Mod. It bundles PICO access, MediaMTX, head-camera RTSP, Pinocchio dual-arm IK, and its runtime libraries. It only requires `com.bxi.basic_actions`; the legacy `bxi_teleop_v2` and separate bringup nodes are not required.

- Mod: [com.bxi.upper_body_teleop](https://github.com/konodoki/com.bxi.upper_body_teleop)
- PICO client: [XRoboToolkit-PICO-1.1.1.apk](https://github.com/XR-Robotics/XRoboToolkit-Unity-Client/releases/download/v1.1.1/XRoboToolkit-PICO-1.1.1.apk)

!!! warning "Safety"
    Validate in simulation before using the real robot. Use a gantry or equivalent protection, clear the arm workspace, keep the emergency stop reachable, and begin with slow, small motions.

## Installation

Install the Mod in the independent directory that is not overwritten by App updates:

```bash
sudo mkdir -p /opt/bxi/mods
sudo git clone https://github.com/konodoki/com.bxi.upper_body_teleop.git /opt/bxi/mods/com.bxi.upper_body_teleop
```

Update an existing checkout:

```bash
cd /opt/bxi/mods/com.bxi.upper_body_teleop
git pull --ff-only
```

If an older project already contains the same Mod in its built-in `mods` or `private_git_mods`, back it up and move it outside the scanned directories. Two copies with the same Mod ID will prevent startup.

## Startup

| Startup method | Project directory | Handling |
|---|---|---|
| Remote controller | `~/bxi_ws/bxi_rl_controller_ros2_example` | Source tree; rebuild the main project after updates. The Mod is loaded from `/opt/bxi/mods`. |
| App | `/opt/bxi/bxi_rl_controller_ros2_example` | App-downloaded prebuilt tree; no manual build. The Mod is loaded from `/opt/bxi/mods`. |

Start the robot and the normal control program. The Mod nodes start automatically when `com.bxi.upper_body_teleop/upper_body_teleop` is entered. Do not run the legacy `elf3_arm_bringup_nohand.launch.py`, `pico_bxi_server`, or `bxi_teleop_v2` scripts separately.

## PICO Connection And Calibration

Use the same PICO connection and body-tracking calibration procedure as Sonic:

1. Secure one Motion Tracker to each leg, with the button/indicator side facing upward, and power them on.
2. Open **Motion Tracker** on the PICO home screen, confirm both trackers are connected, select **Start Calibration**, and complete the guided procedure.
3. Select **Adjust Floor** and align the virtual floor with the physical floor.
4. Open `XRoboToolkit` and connect to the robot through **Network → PC Service** using the robot's LAN IP.
5. Confirm these settings:

   | Section | Option | Setting |
   |---|---|---|
   | Tracking | `Head` | Selected |
   | Tracking | `Controller` | Selected |
   | PICO Motion Tracker | `Mode` | `Full-body` |
   | PICO Motion Tracker | `High-Acc` | Selected |
   | PICO Motion Tracker | `Num` | `2` |
   | Data & Control | `Send` | Selected |

6. Confirm the `Network` status is `WORKING` and the log has no continuous errors. Then enter the Mod state and perform the button calibration.

## Operation

1. From `normal`, press `LB + LT + X` (`btn_10=17`) on the remote controller to enter upper-body teleoperation.
2. On PICO, enable Body Tracking, Controller, and Send. Confirm XRoboToolkit reports `WORKING`.
3. Hold the standard upright posture and press `A+B+X+Y` to calibrate. Successful calibration enters POSE automatically; `A+X` is not required.
4. Hold the left or right grip to take over the corresponding arm. Releasing the grip smoothly returns that arm to its PD standing posture.
5. The left and right triggers control the corresponding grippers. Each state entry performs a low-speed gripper limit calibration.
6. Press `A+B+X+Y` again to recalibrate; both arms return to PD posture during calibration.
7. Exit through the standard system event to `normal`, `PD brake`, `recover`, or `zero-torque`.

`A+X` no longer toggles following mode. If PICO temporarily disconnects, the lower body continues under the gait policy and both arms hold the PD posture.

## Video Streaming

MediaMTX and the head-camera node are managed by the Mod. The default URL is `rtsp://<robot-ip>:2212/video`. Select this address in the PICO app on the same LAN; no separate video script is required.

## Acceptance And Troubleshooting

- Logs should show `mediamtx_server`, `head_camera_rtsp`, `pico_manager`, and `arm_ik_bridge` starting automatically;
- `A+B+X+Y` enters POSE, and the gripped arm follows the controller;
- Triggers control the grippers and child processes stop on state exit.

For a duplicate Mod ID error, keep only `/opt/bxi/mods/com.bxi.upper_body_teleop` and move the old project copy outside the scanned directories. If no PICO data arrives, wake the headset, enable Body Tracking and Send, and confirm `WORKING`.
