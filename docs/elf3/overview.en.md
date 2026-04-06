# Product Introduction

ELF3 is a medium-sized humanoid robot standing 1.45m tall, with motion parameters comparable to a human of similar height.

---

## Product Features

### Mechanical Structure
- **Advanced Actuators**: 31 hollow planetary joint motors across the body, enabling high-dynamic motions such as running, jumping, backflips, and parkour.
- **Skeletal Design**: 1) Minimized weight; 2) Users can attach custom shells to change the robot's appearance and mount additional devices.
- **High Reliability**: Hollow planetary motors significantly reduce ELF3's wiring harness; fall-resistant design meets the reliability demands of robot users.

### Electronics and Communication Architecture
- **High-speed PECI-CANFD Communication**, full-body control frequency >1000Hz
- No EtherCAT protocol support
- CPU: NUC Intel i7 gen 13+ / GPU: optional, supporting motion control + visual end-to-end task control

### Sensors
- IMU, depth camera, LiDAR, RGB camera and other multi-modal sensor interfaces

### Power Management
- Supports battery **hot-swapping**, ensuring continuous operation capability

### Developer Support
- CANFD-based motor communication protocol, allowing developers to directly control the robot's motors
- ROS2-based control framework SDK, enabling one-click deployment of custom control policy networks to simulation environments (Mujoco-based) and real hardware

### Human-Robot Interaction
