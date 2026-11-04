---
seo_title: "ELF3 Depth Camera: Quickly Access RGB and Depth Data"
description: "Get started with ELF3 depth cameras: launch bxi_depth_camera, find color and depth topics, align depth, subscribe with Python, convert depth units, and troubleshoot common issues."
title: Depth Camera
---

# Quickly Access Depth Camera Data

The ELF3 project publishes depth camera data through `bxi_depth_camera`, supporting Intel RealSense and Orbbec Gemini 335 cameras. Applications can subscribe to ROS 2 image topics to receive color images, depth images, and camera intrinsics without calling the vendor SDK directly.

This guide demonstrates **reading one camera on the robot host**, using Python to convert images into NumPy arrays. You only need to launch the camera node to capture images; the motion control program is not required.

## 1. Load the Environment

Choose the project directory for your deployment. These paths match the [Motion Control Development Guide](motioncontrol.md) and [Upper Body Teleoperation](upper_body_teleop.md):

| Deployment | Project directory |
|---|---|
| Source deployment / controller startup | `~/bxi_ws/bxi_rl_controller_ros2_example` |
| Prebuilt program downloaded by the App | `/opt/bxi/bxi_rl_controller_ros2_example` |

Load the ROS and project environments in every new terminal. The following example uses a source deployment; for an App deployment, replace the path after `cd`:

```bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd ~/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash

ros2 pkg prefix bxi_depth_camera
```

On a development computer with a standard ROS 2 Humble installation, replace the first line with `source /opt/ros/humble/setup.bash` and use your own workspace directory. `ros2 pkg prefix` should print the camera package's installation path.

If the camera package has not yet been built in your source workspace, install the project's build dependencies, then run:

```bash
colcon build --merge-install --packages-select bxi_depth_camera
source install/setup.bash
```

The Python example below requires `rclpy`, `sensor_msgs`, `cv_bridge`, and `message_filters`. If these packages are missing from a standard Ubuntu 22.04 / ROS 2 Humble environment, install them with:

```bash
sudo apt install ros-humble-rclpy ros-humble-sensor-msgs \
  ros-humble-cv-bridge ros-humble-message-filters
```

## 2. Start the Camera

First, check whether the camera node is already running:

```bash
ros2 node list
```

If `/depth_camera_manager` is absent, start the camera with depth alignment and frame synchronization enabled:

```bash
ros2 launch bxi_depth_camera cameras.launch.py \
  enable_color:=true \
  enable_depth:=true \
  enable_sync:=true \
  align_depth.enable:=true
```

Keep this terminal running and read the data from a new terminal.

If `example_demo_hw.launch.py` is already running, it already includes the camera node. Use that node instead of starting a second instance. With both color and depth streams enabled by default, enable synchronization and alignment as follows:

```bash
ros2 param set /depth_camera_manager enable_sync true
ros2 param set /depth_camera_manager align_depth.enable true
```

Changing parameters restarts the affected camera streams and briefly interrupts capture. These runtime changes do not persist after the node restarts. If your deployment configuration contains `cameras.<camera_name>.*` overrides, update the corresponding camera-specific parameters.

## 3. Check the Image Topics

A single camera without an explicit serial-number mapping uses the default name `head_depth_camera`:

| Data | Topic | Message type / encoding |
|---|---|---|
| Color image | `/hardware/head_depth_camera/color/image_raw` | `sensor_msgs/msg/Image`, `bgr8` |
| Depth image in the original depth-camera view | `/hardware/head_depth_camera/depth/image_rect_raw` | `sensor_msgs/msg/Image`, `16UC1` |
| Depth image aligned to color | `/hardware/head_depth_camera/aligned_depth_to_color/image_raw` | `sensor_msgs/msg/Image`, `16UC1` |
| Color camera intrinsics | `/hardware/head_depth_camera/color/camera_info` | `sensor_msgs/msg/CameraInfo` |
| Depth camera intrinsics | `/hardware/head_depth_camera/depth/camera_info` | `sensor_msgs/msg/CameraInfo` |
| Aligned depth camera intrinsics | `/hardware/head_depth_camera/aligned_depth_to_color/camera_info` | `sensor_msgs/msg/CameraInfo` |

List the actual topics, then check that images are arriving continuously:

```bash
ros2 topic list
ros2 topic hz /hardware/head_depth_camera/color/image_raw
```

Press `Ctrl+C` to stop the frequency check, then check aligned depth:

```bash
ros2 topic hz /hardware/head_depth_camera/aligned_depth_to_color/image_raw
```

!!! note "Choose the correct depth image"
    If you only need depth data, subscribe directly to `depth/image_rect_raw`; alignment is unnecessary. To look up the depth at a pixel in the color image, use `aligned_depth_to_color/image_raw`, which has the same dimensions and pixel coordinate system as the color image. The original depth image and color image cannot be matched directly using identical pixel indices. Depth alignment is also separate from time synchronization.

When multiple cameras have no explicit mappings, their names may be `SN_<serial>`. Check `ros2 topic list` and adjust the `camera_name` parameter in the example below. Use `ros2 run bxi_depth_camera cameras-inspect` to query serial numbers and supported resolutions and frame rates. This command only enumerates devices; it does not start capture.

## 4. Read Color and Depth Together in Python

Save the following code as `~/read_rgb_depth.py`. It pairs images by message timestamp, produces two NumPy arrays, `rgb` and `depth`, in the callback, and prints their dimensions and the center pixel's depth once per second.

```python
import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from cv_bridge import CvBridge
from message_filters import Subscriber, ApproximateTimeSynchronizer


class CameraReader(Node):
    def __init__(self):
        super().__init__("camera_reader")
        camera_name = self.declare_parameter(
            "camera_name", "head_depth_camera"
        ).value
        # 米 / 数据单位；0 表示尚未指定，只输出原始值。
        self.depth_scale = self.declare_parameter("depth_scale", 0.0).value
        self.bridge = CvBridge()
        base = f"/hardware/{camera_name}"

        self.color_sub = Subscriber(
            self, Image, base + "/color/image_raw",
            qos_profile=qos_profile_sensor_data,
        )
        self.depth_sub = Subscriber(
            self, Image, base + "/aligned_depth_to_color/image_raw",
            qos_profile=qos_profile_sensor_data,
        )
        self.sync = ApproximateTimeSynchronizer(
            [self.color_sub, self.depth_sub],
            queue_size=5,
            slop=0.03,  # 时间戳配对容差为 30 ms。
        )
        self.sync.registerCallback(self.on_frames)

    def on_frames(self, color_msg, depth_msg):
        # rgb: uint8，形状为 (高度, 宽度, 3)，通道顺序为 RGB。
        rgb = self.bridge.imgmsg_to_cv2(color_msg, desired_encoding="rgb8")
        # depth: uint16，形状为 (高度, 宽度)，保留深度数值。
        depth = self.bridge.imgmsg_to_cv2(
            depth_msg, desired_encoding="passthrough"
        )

        y, x = depth.shape[0] // 2, depth.shape[1] // 2
        raw = int(depth[y, x])  # 数组索引为 [行 y, 列 x]。
        if raw == 0:
            value = "invalid"
        elif self.depth_scale > 0:
            value = f"{raw * self.depth_scale:.3f} m"
        else:
            value = f"{raw} (raw)"
        self.get_logger().info(
            f"RGB={rgb.shape}, depth={depth.shape}, center={value}",
            throttle_duration_sec=1.0,
        )
        # 在这里处理 rgb 和 depth，例如识别目标或读取目标像素深度。


def main():
    rclpy.init()
    node = CameraReader()
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

Run it in a new terminal after loading the environment from step 1:

```bash
/usr/bin/python3 ~/read_rgb_depth.py
```

Once images arrive, the output will look like this. Actual dimensions depend on the profiles negotiated with the device:

```text
RGB=(1080, 1920, 3), depth=(1080, 1920), center=1234 (raw)
```

`rgb[y, x]` contains the pixel's RGB color, and `depth[y, x]` contains its corresponding depth value. If subsequent processing uses OpenCV's BGR interfaces, change `desired_encoding="rgb8"` to `"bgr8"`. The example receives images using `qos_profile_sensor_data` and allows a timestamp difference of approximately 30 ms between the two streams. This is approximate pairing; it does not guarantee identical exposure times.

To select another logical camera name, such as `body_depth_camera` already mapped in your deployment:

```bash
/usr/bin/python3 ~/read_rgb_depth.py --ros-args \
  -p camera_name:=body_depth_camera
```

## 5. Convert Depth to Meters

`16UC1` only specifies a single-channel, unsigned 16-bit integer image. The encoding alone does not determine its physical units. The two backends currently publish depth as follows:

| Backend | Depth values in the topic | Example's `depth_scale` |
|---|---|---|
| Orbbec | The driver has converted SDK data to millimeters | `0.001` |
| RealSense | The current implementation publishes SDK depth values directly | The device's actual meters-per-unit scale |

For Orbbec, run the following command directly. For RealSense, use the same parameter only after confirming that the device scale is `0.001 m/unit`:

```bash
/usr/bin/python3 ~/read_rgb_depth.py --ros-args -p depth_scale:=0.001
```

A depth value of `1234` will then be displayed as `1.234 m`. A depth value of `0` means an invalid measurement, not zero distance. These values represent Z depth along the camera's optical axis.

If the RealSense scale is unknown, you can initially read the raw values. To validate the device, first stop any capture program using that camera, then run:

```bash
ros2 run bxi_depth_camera cameras-validate --serial "YOUR_SERIAL"
```

Replace `YOUR_SERIAL` with the actual serial number. This tool starts and validates each stream profile in turn, which may take several minutes. After successfully reading depth, the summary's `depth scale: raw x ... m` line gives the conversion from raw SDK values to meters. Restart camera capture after validation. Orbbec topics are already normalized to millimeters; do not apply the SDK's raw scale to topic data again.

## Troubleshooting

| Symptom | What to check |
|---|---|
| `bxi_depth_camera` cannot be found | Confirm that your deployment includes the package and that you sourced its `install/setup.bash`. For a source deployment, build it as described in step 1. |
| No camera topics | Check the USB connection, power, and startup logs. Run `cameras-inspect` to confirm that the device can be enumerated. |
| Device permission error | On first deployment, run `ros2 run bxi_depth_camera install-udev-rules`, then reconnect the camera after installing the rules. |
| Color arrives but aligned depth does not | Confirm that color, depth, and `align_depth.enable` are all enabled, and check for camera-specific parameter overrides. |
| The script produces no output | Check both topic names and frequencies. Confirm that `enable_sync` is enabled and that timestamps from the two streams can be paired. |
| Camera names differ from the example with multiple cameras | Check `ros2 topic list` and use `camera_name` to select the actual logical name or `SN_<serial>`. |
| High processing or transmission latency | Use `cameras-inspect` to list supported profiles, then choose a lower-resolution `rgb_camera.color_profile`. Aligned depth dimensions follow the color resolution. |

For subscriptions across hosts, also ensure that the network, ROS discovery configuration, and `ROS_DOMAIN_ID` match the publisher. The example above assumes both programs run on the same host.
