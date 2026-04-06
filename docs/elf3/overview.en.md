---
title: Product Introduction
---

# ELF 3

ELF 3 is a medium-sized humanoid robot developed in-house by BXI Robotics, standing 1.45 m tall with motion parameters comparable to a human of similar height. It is designed for high-dynamic movement and open-platform development.

| ![ELF 3 Front View](../assets/elf3/robo2.png) | ![ELF 3 Side View](../assets/elf3/robo1.png) |
|:---:|:---:|
| Front View | Side View |

---

## Key Highlights

- **High-Dynamic Motion**: 31 BXI hollow planetary joint motors across the body, enabling running, jumping, backflips, and parkour
- **Skeletal Lightweight Design**: Minimized weight; custom shells can be attached to change appearance and mount additional devices
- **High Reliability**: Hollow cable routing greatly reduces the wiring harness; built-in fall-resistant design
- **High-Speed Bus**: PCIE-CANFD with full-body control frequency > 1000 Hz
- **Hot-Swap Battery**: Replace batteries without powering off, ensuring continuous operation
- **Open Development Interface**: CANFD MIT protocol for direct motor control + ROS2 SDK + one-click MuJoCo simulation deployment

---

## Full Specifications

### Dimensions & Performance

| Item | Specification |
| :--- | :--- |
| **Height** | 1450 mm |
| **Width** | 450 mm |
| **Depth** | 280 mm |
| **Thigh Length** | 320 mm |
| **Shin Length** | 320 mm |
| **Upper Arm Length** | 240 mm |
| **Forearm Length** | 240 mm |
| **Total Weight** | ~38 kg |
| **Arm Payload** | 5 kg extended (×10 continuous); 10 kg elbow-supported (×10 continuous) |
| **Max Speed** | > 4 m/s (~13 km/h) |

---

## Mechanical Structure

### Degrees of Freedom

| Item | Specification |
| :--- | :--- |
| **Total DOF** | 31 (including 2-DOF neck) |
| **DOF per Leg** | 6 (Hip XYZ × 3 + Knee Y × 1 + Ankle XY × 2) |
| **DOF per Arm** | 7 (Shoulder YXZ × 3 + Elbow Y × 1 + Wrist XYZ × 3) |
| **Motor Series** | BXI Hollow Planetary |

### Joint Motor Selection

> `l` = left, `r` = right. `l/r` denotes a symmetric pair — one joint on each side.

| Joint | Motor | Peak Torque |
| :--- | :--- | :--- |
| `waist_z_joint` | BXI8515-19 | 120–150 Nm |
| `waist_x_joint`, `waist_y_joint` | BXI7010-19 × 2 (dual motor) | 2 × 50 Nm each |
| `l/r_hip_x_joint`, `l/r_hip_y_joint`, `l/r_knee_y_joint` | BXI8515-19 | 150 Nm |
| `l/r_hip_z_joint` | BXI7010-19 | 50 Nm |
| `l/r_ankle_y_joint`, `l/r_ankle_x_joint` | BXI5018-19 × 2 (parallel) | > 50 Nm combined |
| `l/r_shoulder_y_joint`, `l/r_shoulder_x_joint`, `l/r_elbow_y_joint` | BXI7010-19 | 50 Nm |
| `l/r_shoulder_z_joint`, `l/r_wrist_x_joint`, `l/r_wrist_y_joint`, `l/r_wrist_z_joint` | BXI5014-19 | 25 Nm |
| `neck_z_joint`, `neck_y_joint` | BXI5014-19 | 25 Nm |

---

## Electrical System

| Item | Specification |
| :--- | :--- |
| **Operating Voltage** | 48 V |
| **Rated Current** | 50 A |
| **Max Current** | > 100 A |
| **Battery Capacity** | 432 Wh, lithium |
| **Battery Life** | ~1 hour walking |
| **Hot-Swap** | Supported |

---

## Computing & Perception

| Item | Specification |
| :--- | :--- |
| **CPU** | NUC Intel i7-1370p (ARM optional) |
| **NPU/GPU** | NVIDIA Jetson series supported (optional or user-installed) |
| **Control Module** | FPGA PCIE-CAN |
| **IMU** | Onboard |
| **Depth Camera** | Intel RealSense D435i |
| **LiDAR** | Optional (Livox Mid360) |
| **Microphone** | HAOKAI 8-array omnidirectional microphone |
| **Speaker** | Yuexin active speaker (DC 5V) |
| **Wi-Fi / Bluetooth** | Onboard |

---

## Software Ecosystem

| Item | Specification |
| :--- | :--- |
| **OS** | Ubuntu 22.04 |
| **Motor Interface** | CANFD SDK, MIT protocol (torque / position / velocity / temperature) |
| **Robot Framework** | ROS2-based hardware control node SDK |
| **Simulation** | MuJoCo-based RL training & deployment framework |
| **Pre-installed Algorithm** | Flat-ground walking and running |
| **URDF** | Provided |

---

## Accessories

| Item | Notes |
| :--- | :--- |
| **Dexterous Hand** | Paid add-on (independent unit) |
| **Xbox-compatible Gamepad** | Included |
| **Tablet Control App** | Included |

---

## Full Joint Parameters

| Joint | Min (rad) | Max (rad) | Peak Torque (Nm) | Peak Speed (rad/s) | Inertia (kg·m²) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| waist_y_joint | −0.5236 | 0.5236 | 90 | 20 | 0.0274702 |
| waist_x_joint | −0.2618 | 0.2618 | 100 | 20 | 0.0412054 |
| waist_z_joint | −2.8798 | 2.8798 | 150 | 20 | 0.044688 |
| l_hip_y_joint | −2.8798 | 2.8798 | 150 | 20 | 0.044688 |
| l_hip_x_joint | −0.48869 | 3.0543 | 150 | 20 | 0.044688 |
| l_hip_z_joint | −2.8798 | 2.8798 | 45 | 20 | 0.0137351 |
| l_knee_y_joint | −0.087266 | 2.618 | 150 | 20 | 0.044688 |
| l_ankle_y_joint | −0.87266 | 0.7854 | 40 | 20 | 0.00848397 |
| l_ankle_x_joint | −0.34907 | 0.34907 | 15 | 20 | 0.00551458 |
| r_hip_y_joint | −2.8798 | 2.8798 | 150 | 20 | 0.044688 |
| r_hip_x_joint | −3.0543 | 0.48869 | 150 | 20 | 0.044688 |
| r_hip_z_joint | −2.8798 | 2.8798 | 45 | 20 | 0.0137351 |
| r_knee_y_joint | −0.087266 | 2.618 | 150 | 20 | 0.044688 |
| r_ankle_y_joint | −0.87266 | 0.7854 | 40 | 20 | 0.00848397 |
| r_ankle_x_joint | −0.34907 | 0.34907 | 15 | 20 | 0.00551458 |
| l_shoulder_y_joint | −2.8798 | 2.8798 | 45 | 20 | 0.0137351 |
| l_shoulder_x_joint | −0.34907 | 3.0543 | 45 | 20 | 0.0137351 |
| l_shoulder_z_joint | −2.8798 | 2.8798 | 21 | 20 | 0.00424198 |
| l_elbow_y_joint | −0.95993 | 1.6581 | 45 | 20 | 0.0137351 |
| l_wrist_x_joint | −2.8798 | 2.8798 | 21 | 20 | 0.00424198 |
| l_wrist_y_joint | −1.309 | 1.309 | 21 | 20 | 0.00424198 |
| l_wrist_z_joint | −0.7854 | 0.7854 | 21 | 20 | 0.00424198 |
| r_shoulder_y_joint | −2.8798 | 2.8798 | 45 | 20 | 0.0137351 |
| r_shoulder_x_joint | −3.0543 | 0.34907 | 45 | 20 | 0.0137351 |
| r_shoulder_z_joint | −2.8798 | 2.8798 | 21 | 20 | 0.00424198 |
| r_elbow_y_joint | −0.95993 | 1.6581 | 45 | 20 | 0.0137351 |
| r_wrist_x_joint | −2.8798 | 2.8798 | 21 | 20 | 0.00424198 |
| r_wrist_y_joint | −1.309 | 1.309 | 21 | 20 | 0.00424198 |
| r_wrist_z_joint | −0.7854 | 0.7854 | 21 | 20 | 0.00424198 |
| neck_z_joint | −1.57 | 1.57 | 21 | 20 | 0.00424198 |
| neck_y_joint | −0.7854 | 0.7854 | 21 | 20 | 0.00424198 |
