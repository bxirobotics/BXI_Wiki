---
seo_title: "ELF3 bxi_imu: ROS 2 IMU Data Interface and Subscription"
description: "Use the ELF3 public IMU interface: ROS 2 topics, message fields, units, coordinate mapping, QoS, Python subscription, controller timeout and tilt protection, and CSV recording."
title: IMU (bxi_imu)
---

# bxi_imu: IMU Data Interface

> Last updated: 2026-11-05 14:22 (UTC+8)

`bxi_imu` publishes IMU data through ROS 2. Applications subscribe to a common topic to receive orientation, angular velocity and linear acceleration.

## 1. Interface Overview

| Item | Interface |
|---|---|
| ROS 2 package | `bxi_imu` |
| Standalone node name | `/imu_node` |
| Launch file | `imu.launch.py` |
| Main topic | `/hardware/imu_data` |
| Main message type | `sensor_msgs/msg/Imu` |
| Default frame | `imu_link` |
| QoS | `SensorDataQoS`; use `best_effort` for subscriptions |

Applications use the published message fields and coordinate frame. If the robot already provides valid IMU data, subscribe to the existing topic directly.

## 2. Output Topics

| Default topic | Message type | Content | Default publishing |
|---|---|---|---|
| `/hardware/imu_data` | `sensor_msgs/msg/Imu` | Orientation, angular velocity and linear acceleration | Enabled |
| `/euler_data` | `geometry_msgs/msg/Vector3Stamped` | Euler angles: roll, pitch and yaw | Disabled |
| `/magnetic_data` | `sensor_msgs/msg/MagneticField` | Three-axis magnetic field | Disabled |
| `/temp_data` | `sensor_msgs/msg/Temperature` | Temperature | Disabled |
| `/pressure_data` | `sensor_msgs/msg/FluidPressure` | Pressure | Disabled |

Optional messages depend on deployment settings and available data fields. A topic appearing in the graph does not establish that it sends messages continuously. Confirm actual message reception.

## 3. Environment and Startup

Load ROS and the project environment in each new terminal. This example uses standard ROS 2 Humble. Replace the workspace path with the actual deployment location. On a robot using the BXI ROS environment, replace the first line with `source /opt/bxi/bxi_ros2_pkg/setup.bash`.

```bash
source /opt/ros/humble/setup.bash
cd ~/bxi_ws/bxi_controller_ros2
source install/setup.bash
ros2 pkg prefix bxi_imu
```

For a new source deployment that has not been built, run this after loading ROS and before loading `install/setup.bash`:

```bash
colcon build --merge-install --symlink-install --packages-select bxi_imu
```

First check existing data:

```bash
ros2 topic info -v /hardware/imu_data
ros2 topic echo --once --qos-reliability best_effort \
  /hardware/imu_data sensor_msgs/msg/Imu
```

`echo --once` waits for one actual message. Press `Ctrl+C` to stop waiting. To start the IMU separately, run:

```bash
ros2 launch bxi_imu imu.launch.py
```

If the control program manages IMU startup, use its existing topic. Reading IMU data alone does not require launching the full robot control program.

## 4. Message Fields and Units

### 4.1 Main IMU Message

`/hardware/imu_data` uses `sensor_msgs/msg/Imu`:

| Field | Meaning | Unit or convention |
|---|---|---|
| `header.stamp` | Host system time when decoding completes | `sec` and `nanosec`; not the hardware sampling time |
| `header.frame_id` | Coordinate frame of the data | Default: `imu_link` |
| `orientation.x/y/z/w` | Orientation quaternion | Dimensionless; ROS field order is `x, y, z, w` |
| `angular_velocity.x/y/z` | Three-axis angular velocity | `rad/s` |
| `linear_acceleration.x/y/z` | Three-axis linear acceleration | `m/s²` |
| `orientation_covariance` | Orientation covariance | Currently not estimated; initialized to `0` |
| `angular_velocity_covariance` | Angular velocity covariance | Currently not estimated; initialized to `0` |
| `linear_acceleration_covariance` | Acceleration covariance | Currently not estimated; initialized to `0` |

Zero covariance does not mean noiseless measurements. Configure measurement noise according to your filtering or fusion requirements. The main message has no separate validity flag. Applications should check both values and whether updates continue to arrive.

### 4.2 Optional Messages

| Topic | Field | Unit or meaning |
|---|---|---|
| `/euler_data` | `vector.x/y/z` | Roll, pitch and yaw respectively, in `rad` |
| `/magnetic_data` | `magnetic_field.x/y/z` | Magnetic field in `T` |
| `/temp_data` | `temperature` | Temperature in `°C` |
| `/pressure_data` | `fluid_pressure` | ROS specifies `Pa`; confirm the deployed data units before quantitative use |

## 5. Coordinate Directions and Mapping

Published messages identify their coordinate frame through `header.frame_id`, which defaults to `imu_link`. Deployment settings determine the axis mapping. Applications receive data with that mapping already applied.

### 5.1 Meaning of identity

When `axis_mapping` is `identity`, the original IMU axis directions are preserved:

```text
output_x = imu_x
output_y = imu_y
output_z = imu_z
```

Axes are neither exchanged nor inverted, and installation angles are not automatically compensated. Use this setting when the mounted IMU axes already match the intended output directions.

### 5.2 Another Mapping Example

For example, `axis_mapping` set to `-y,x,z` means:

```text
output_x = -imu_y
output_y =  imu_x
output_z =  imu_z
```

The mapping applies consistently to angular velocity, acceleration, magnetic field and orientation. Euler angles are recomputed from the transformed orientation. Applications using the output frame should avoid applying the same mapping again.

These examples explain deployment settings. Changing only `frame_id` does not change numeric directions, and this node does not publish TF between frames.

## 6. QoS and Communication Environment

Publishers use `SensorDataQoS`. Use `best_effort` for command-line subscriptions and `qos_profile_sensor_data` for Python subscriptions.

```bash
ros2 topic echo --once --qos-reliability best_effort \
  /hardware/imu_data sensor_msgs/msg/Imu
```

If a controller service starts the robot, match its `ROS_DOMAIN_ID`, `RMW_IMPLEMENTATION` and DDS network settings in the subscriber terminal. See [System Settings](overview.en.md).

For subscriptions across hosts, also check network interfaces and DDS connectivity.

## 7. Python Subscriber Example

Save the following as `read_imu.py`. It receives messages continuously, prints the latest data once per second, and checks callback arrival times to detect a gap longer than one second. This one-second threshold is only for the example display.

```python
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Imu


class ImuReader(Node):
    def __init__(self):
        super().__init__("imu_reader")
        self.latest = None
        self.last_received = None
        self.subscription = self.create_subscription(
            Imu, "/hardware/imu_data", self.on_imu, qos_profile_sensor_data
        )
        self.timer = self.create_timer(1.0, self.report)

    def on_imu(self, msg):
        self.latest = msg
        self.last_received = time.monotonic()

    def report(self):
        if self.latest is None:
            self.get_logger().info("Waiting for IMU data")
            return
        age = time.monotonic() - self.last_received
        if age > 1.0:
            self.get_logger().warning(f"No IMU update for {age:.2f} s")
            return
        q = self.latest.orientation
        w = self.latest.angular_velocity
        a = self.latest.linear_acceleration
        self.get_logger().info(
            f"frame={self.latest.header.frame_id} "
            f"q(x,y,z,w)=({q.x:.4f},{q.y:.4f},{q.z:.4f},{q.w:.4f}) "
            f"gyro(rad/s)=({w.x:.3f},{w.y:.3f},{w.z:.3f}) "
            f"acc(m/s^2)=({a.x:.3f},{a.y:.3f},{a.z:.3f})"
        )


def main():
    rclpy.init()
    node = ImuReader()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
```

Load the runtime environment and run:

```bash
python3 read_imu.py
```

## 8. Data Validity and Rate

Before publishing, the node checks that all quaternion components are finite and that the norm is within the allowed range. The default range is `0.9..1.1`. Samples that fail are not published. Accepted quaternions are not automatically normalized, and this check does not validate every other sensor field.

Applications should track reception times to detect whether data continues to update. Inspect the received rate with:

```bash
ros2 topic hz /hardware/imu_data
```

The output rate depends on the current device configuration and runtime conditions. Avoid assuming a fixed rate in subscriber code. `ros2 topic hz` reports the subscriber's received rate, which host scheduling and DDS communication can affect.

Startup timeout messages support diagnosis. An application's freshness check should use callback reception times. `header.stamp` can help analyze host decoding times but does not represent hardware sampling time.

## 9. IMU Protection in the Controller

This section follows the `bxi_example_py_elf3_demo` control program launched by `example_demo_hw.launch.py` in `bxi_example_py_elf3`. It subscribes to `/hardware/imu_data`, validates incoming data independently and restricts control states when a fault occurs. The startup wait and runtime loss protection below are enabled when `topic_prefix` starts with `hardware/`. Check other program entry points separately.

### 9.1 Incoming Data Validation

For each received IMU message, the controller checks:

- All four quaternion components are finite, and the norm is within `0.9..1.1`.
- All six angular velocity and acceleration components are finite.

Invalid frames are discarded without updating control observations or the last valid IMU reception time. The `dropping invalid IMU frame` warning includes the cumulative count and is throttled to five-second intervals.

A topic that continuously sends invalid messages can therefore still trigger loss protection.

### 9.2 Wait for Valid Data Before Startup

Hardware control startup requires at least one IMU frame passing these checks. Until then, the program waits before proceeding with robot resets and control startup.

By default, it logs `waiting for IMU data` every two seconds and one `IMU startup timeout` error after `15 s`. This startup timeout only logs an error. The program keeps waiting instead of skipping the check or exiting automatically. Subsequent startup steps also require joint data and other conditions.

### 9.3 Runtime Loss Detection

The controller records valid frame arrival times using the host monotonic clock. Before reading inputs in a control cycle, it checks:

```text
Current monotonic time - Last valid reception time ≥ imu_runtime_timeout_sec
```

The default threshold is `0.1 s`, or `100 ms`. At the threshold, the program logs `IMU data timeout`, latches the fault and forcibly requests `com.bxi.basic_actions/imu_protection`.

Checks run with control cycles, so scheduling affects actual response latency. Detection uses valid message callback arrival times, rather than `header.stamp`. The one-second display threshold in the section 7 subscriber example is separate from the controller's protection threshold.

### 9.4 Protection Commands and Recovery

On entering IMU loss protection, the state captures the joint positions currently recorded by the controller and continuously generates these joint commands:

| Command field | Value generated by the protection state |
|---|---|
| Target position | Captured joint positions, held unchanged |
| Position gain `kp` | Default: `20.0` |
| Velocity gain `kd` | Default: `1.0` |
| Target velocity | `0` |
| Feed-forward torque | `0` |

This is a low-stiffness hold at fixed joint positions. Once latched, the controller suppresses and clears pending remote state events. The default state configuration also provides no outgoing routes from this state. Restored IMU data does not resume walking automatically, and ordinary state selection buttons do not release the protection.

The code reserves a `release_imu_protection()` method, disabled by default through `/imu_protection_allow_release=false`. When explicitly enabled and valid IMU data remains within the timeout threshold, calling it attempts to clear the latch and switch state. The default target is `com.bxi.basic_actions/zero_torque`. This is an in-process method; there is currently no corresponding standalone ROS recovery service.

### 9.5 Tilt Protection During Walking

The `normal` walking state and the `forward_back` state that inherits its update logic also calculate roll and pitch from the IMU orientation. If either absolute angle exceeds `π/3`, or `60°`, they request `com.bxi.basic_actions/zero_torque`.

The zero-torque state generates `kp=0`, `kd=0` and zero feed-forward torque. Tilt protection and IMU loss protection have different triggers and target states. This tilt check belongs to the listed walking states' update logic and is not a global check for every action state.

### 9.6 Parameters, Launch and Scope

| Setting | Default | Purpose |
|---|---|---|
| Controller node parameter `/imu_startup_timeout_sec` | `15.0` | Log one error after this startup wait and continue waiting |
| Controller node parameter `/imu_runtime_timeout_sec` | `0.1` | Valid frame timeout in seconds; must be positive |
| Controller node parameter `/imu_protection_allow_release` | `false` | Allow the in-process recovery method to clear the latch |
| Protection state settings `kp`, `kd` | `20.0`, `1.0` | Joint gains generated by the protection state |

The current `example_demo_hw.launch.py` exposes an `imu_runtime_timeout_sec` launch argument. For example, to launch the full hardware and controller with a separate IMU data source:

```bash
ros2 launch bxi_example_py_elf3 example_demo_hw.launch.py \
  enable_imu:=false imu_runtime_timeout_sec:=0.1
```

This command does not launch a separate `bxi_imu` instance. Supply IMU data in another terminal or use the existing robot startup flow. The other controller node parameters in the table are not exposed as individual arguments by this launch file; set them in the controller node's parameter configuration. Protection gains belong to the basic actions state configuration. Settings are read during initialization, so restart the controller after changes.

Protection checks whether valid messages keep arriving. It does not check whether values change or whether `header.stamp` is stale or increasing. Repeated old but valid values can keep refreshing the reception time.

The current IMU protection state does not automatically disable the [external joint command override interface](mod_api_31dof_control.en.md). Final joint commands still pass through the override logic. The table describes commands generated by the protection state; a latched state does not close every control input channel.

## 10. CSV Recording and Runtime Logs

Control CSV recording at startup:

```bash
# Follow deployment settings
ros2 launch bxi_imu imu.launch.py imu_record_enabled:=auto

# Disable recording
ros2 launch bxi_imu imu.launch.py imu_record_enabled:=false

# Enable recording
ros2 launch bxi_imu imu.launch.py imu_record_enabled:=true
```

Run one command as needed. The recording switch does not change ROS message fields.

| Item | Default location or behavior |
|---|---|
| CSV directory | `/var/log/bxi_log/imu/data/` |
| Controller startup log directory | `/var/log/bxi_log/imu/` |
| Example filename | `imu_data_20261105_140000_0001.csv` |
| File creation | One file per IMU process startup |
| Retention | Keep the latest ten matching CSV files by default |

CSV includes the following data:

| Field | Meaning |
|---|---|
| `receive_time_ns` | System time when the writer thread generates the row, in nanoseconds |
| `ros_stamp_sec`, `ros_stamp_nanosec` | System time assigned during decoding |
| `quaternion_valid`, `drop_reason` | Quaternion validation result and drop reason |
| `quaternion_w/x/y/z`, `quaternion_norm` | Quaternion in the output frame and its norm; CSV places `w` first |
| `euler_roll/pitch/yaw` | Euler angles; zero values do not establish field availability |
| `angular_velocity_*`, `linear_acceleration_*` | Angular velocity and acceleration in the output frame |
| `arrival_gap_ms` | Interval between adjacent samples in the host recording logic |

CSV can include samples that failed quaternion validation and were not published to ROS, helping diagnose dropped frames. A full recording queue or write failure can leave gaps. Files do not roll over by size or duration during a process run.

## 11. Troubleshooting

| Symptom | Check |
|---|---|
| `bxi_imu` cannot be found | Load the correct ROS and project environments; run `ros2 pkg prefix bxi_imu` |
| Topic exists without data | Wait for an actual message with `echo --once`; check publishing settings and logs |
| Existing data cannot be received | Check QoS, `ROS_DOMAIN_ID`, RMW and DDS network settings |
| Orientation or axis directions differ from expectations | Check `header.frame_id`, the deployed mapping and whether the application repeats the transform |
| Optional Euler angle, magnetic field or other messages are missing | Confirm that the output is enabled and the data contains the relevant fields |
| Displayed values remain stale | Track callback reception times to detect whether messages continue to update |
| Invalid quaternion warnings appear | Inspect the norm, validity flag and drop reason in runtime logs and CSV |
| Received rate varies | Check runtime logs, host load, communication settings and CSV intervals |
| Controller keeps waiting for IMU | Confirm frames pass quaternion and vector finiteness checks; startup timeout still leaves the program waiting |
| Walking remains unavailable after IMU recovery | Check for latched IMU loss protection; restored data does not release it automatically |
| Walking switches to zero torque | Check whether roll or pitch exceeds `60°`; distinguish tilt protection from loss protection |
| CSV files are missing | Check the recording switch, directory write permissions and recorder warnings |

First confirm actual messages on `/hardware/imu_data`, then verify fields, coordinate directions and reception rate.
