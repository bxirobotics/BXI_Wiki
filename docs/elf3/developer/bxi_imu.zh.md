---
seo_title: "ELF3 bxi_imu：ROS 2 IMU 数据接口与订阅方法"
description: "介绍 ELF3 统一 IMU 对外接口，包括 ROS 2 话题、消息字段、数据单位、坐标方向、QoS、Python 订阅、控制程序失联与倾斜保护及 CSV 记录。"
title: IMU（bxi_imu）
---

# bxi_imu：IMU 数据接口

> 文档更新时间：2026-11-05 14:22（UTC+8）

`bxi_imu` 通过 ROS 2 发布 IMU 数据。应用程序订阅统一话题即可获取姿态、角速度和线加速度。

## 1. 接口概述

| 项目 | 接口 |
|---|---|
| ROS 2 包 | `bxi_imu` |
| 独立节点名称 | `/imu_node` |
| 启动文件 | `imu.launch.py` |
| 主话题 | `/hardware/imu_data` |
| 主消息类型 | `sensor_msgs/msg/Imu` |
| 默认坐标系 | `imu_link` |
| QoS | `SensorDataQoS`，订阅端使用 `best_effort` |

应用程序使用发布后的消息字段和坐标系。机器人已经提供有效 IMU 数据时，可直接订阅现有话题。

## 2. 输出话题

| 默认话题 | 消息类型 | 内容 | 默认发布 |
|---|---|---|---|
| `/hardware/imu_data` | `sensor_msgs/msg/Imu` | 姿态、角速度、线加速度 | 开启 |
| `/euler_data` | `geometry_msgs/msg/Vector3Stamped` | 欧拉角 roll、pitch、yaw | 关闭 |
| `/magnetic_data` | `sensor_msgs/msg/MagneticField` | 三轴磁场 | 关闭 |
| `/temp_data` | `sensor_msgs/msg/Temperature` | 温度 | 关闭 |
| `/pressure_data` | `sensor_msgs/msg/FluidPressure` | 气压 | 关闭 |

附加话题是否有消息取决于部署配置和实际可用的数据字段。话题出现在列表中不代表正在持续发布；应用应确认收到了真实消息。

## 3. 环境与启动

在每个新终端加载 ROS 和工程环境。以下使用标准 ROS 2 Humble，工作空间路径按实际部署位置替换；机器人使用 BXI ROS 环境时，第一行改为 `source /opt/bxi/bxi_ros2_pkg/setup.bash`。

```bash
source /opt/ros/humble/setup.bash
cd ~/bxi_ws/bxi_controller_ros2
source install/setup.bash
ros2 pkg prefix bxi_imu
```

首次从源码部署且尚未构建时，在加载 ROS 环境后、加载 `install/setup.bash` 前执行：

```bash
colcon build --merge-install --symlink-install --packages-select bxi_imu
```

先检查现有数据：

```bash
ros2 topic info -v /hardware/imu_data
ros2 topic echo --once --qos-reliability best_effort \
  /hardware/imu_data sensor_msgs/msg/Imu
```

`echo --once` 等待一条真实消息，可用 `Ctrl+C` 结束等待。需要单独启动 IMU 时执行：

```bash
ros2 launch bxi_imu imu.launch.py
```

若机器人由控制程序管理 IMU 启动，应使用该程序提供的现有话题。单独读取 IMU 不需要启动完整机器人控制程序。

## 4. 消息字段与单位

### 4.1 IMU 主消息

`/hardware/imu_data` 使用 `sensor_msgs/msg/Imu`：

| 字段 | 含义 | 单位或约定 |
|---|---|---|
| `header.stamp` | 主机完成数据解码时的系统时间 | `sec` 与 `nanosec`，不是设备硬件采样时间 |
| `header.frame_id` | 数据所属坐标系 | 默认 `imu_link` |
| `orientation.x/y/z/w` | 姿态四元数 | 无量纲，ROS 字段顺序为 `x, y, z, w` |
| `angular_velocity.x/y/z` | 三轴角速度 | `rad/s` |
| `linear_acceleration.x/y/z` | 三轴线加速度 | `m/s²` |
| `orientation_covariance` | 姿态协方差 | 当前未估计，初始化值为 `0` |
| `angular_velocity_covariance` | 角速度协方差 | 当前未估计，初始化值为 `0` |
| `linear_acceleration_covariance` | 线加速度协方差 | 当前未估计，初始化值为 `0` |

协方差为零不表示测量没有噪声。需要滤波或融合时，应根据应用要求设置测量噪声。主消息没有单独的有效性标志，应用需同时检查数值与消息是否持续更新。

### 4.2 附加消息

| 话题 | 字段 | 单位或含义 |
|---|---|---|
| `/euler_data` | `vector.x/y/z` | 分别为 roll、pitch、yaw，单位 `rad` |
| `/magnetic_data` | `magnetic_field.x/y/z` | 磁场，单位 `T` |
| `/temp_data` | `temperature` | 温度，单位 `°C` |
| `/pressure_data` | `fluid_pressure` | ROS 消息约定单位为 `Pa`；用于定量计算前确认当前部署的数据单位 |

## 5. 坐标方向与映射

对外消息使用 `header.frame_id` 标识坐标系，默认值为 `imu_link`。数值方向由部署时的方向映射配置决定，应用读取的是已经完成方向映射的数据。

### 5.1 identity 的含义

`axis_mapping` 为 `identity` 时，保持 IMU 原始坐标轴方向：

```text
output_x = imu_x
output_y = imu_y
output_z = imu_z
```

它不交换轴、不取反，也不会自动补偿安装角度。使用该配置时，IMU 安装方向应已经与期望输出方向一致。

### 5.2 其他映射示例

例如 `axis_mapping` 为 `-y,x,z` 时：

```text
output_x = -imu_y
output_y =  imu_x
output_z =  imu_z
```

映射会同步作用于角速度、线加速度、磁场和姿态；欧拉角由变换后的姿态重新计算。应用使用输出坐标系时，应避免再次执行同样的映射。

方向映射属于部署配置，以上为含义说明。仅修改 `frame_id` 不会改变数据方向，该节点也不负责发布坐标系之间的 TF。

## 6. QoS 与通信环境

发布者使用 `SensorDataQoS`。命令行订阅使用 `best_effort`，Python 订阅使用 `qos_profile_sensor_data`。

```bash
ros2 topic echo --once --qos-reliability best_effort \
  /hardware/imu_data sensor_msgs/msg/Imu
```

通过遥控器服务启动机器人时，订阅终端需与服务使用一致的 `ROS_DOMAIN_ID`、`RMW_IMPLEMENTATION` 和 DDS 网络配置。相关配置见[系统设置说明](overview.zh.md)。

跨主机订阅还需检查网络接口及 DDS 通信是否可达。

## 7. Python 订阅示例

将下面代码保存为 `read_imu.py`。示例持续接收消息，每秒打印最新数据，并根据回调接收时间判断是否超过一秒没有更新。这个一秒阈值仅用于示例显示。

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

加载运行环境后执行：

```bash
python3 read_imu.py
```

## 8. 数据有效性与频率

发布前会检查四元数各分量是否为有限值，以及模长是否在允许范围内。默认允许范围为 `0.9..1.1`，不合格样本不会发布。通过校验的四元数不会自动归一化；该检查也不代表所有传感器字段都已经通过有效性检查。

应用应根据实际接收时间检测数据是否持续更新。可在终端查看接收频率：

```bash
ros2 topic hz /hardware/imu_data
```

输出频率取决于当前设备配置和实际运行情况，不应在订阅程序中假设固定频率。`ros2 topic hz` 显示订阅端收到的频率，会受主机调度和 DDS 通信影响。

启动日志中的超时提示用于诊断。应用自己的数据新鲜度检查应基于回调接收时间；`header.stamp` 可用于分析主机解码时间，但不代表硬件采样时刻。

## 9. 控制程序的 IMU 保护

本节依据 `bxi_example_py_elf3` 包中由 `example_demo_hw.launch.py` 启动的 `bxi_example_py_elf3_demo` 控制程序。它订阅 `/hardware/imu_data`，在接收端独立检查数据，并在异常时限制控制状态。以下启动等待和失联保护在 `topic_prefix` 以 `hardware/` 开头时启用；其他程序入口需分别核对实现。

### 9.1 接收数据校验

控制程序接收到每一帧 IMU 消息时，会检查：

- 四元数的四个分量均为有限值，模长位于 `0.9..1.1`。
- 角速度和线加速度的六个分量均为有限值。

不合格帧直接丢弃，不更新控制观测值，也不刷新“最后一次收到有效 IMU 数据”的时间。日志 `dropping invalid IMU frame` 会输出累计丢弃数，并按五秒间隔限频。

因此，即使话题持续发送消息，持续无效的数据仍可能触发失联保护。

### 9.2 启动前等待有效数据

实机控制启动前，必须先收到至少一帧通过上述检查的 IMU 数据。尚未收到时，控制程序保持等待，不进入后续机器人复位和控制启动流程。

默认每两秒提示 `waiting for IMU data`；等待达到 `15 s` 时输出一次 `IMU startup timeout` 错误。该启动超时只记录错误，程序仍继续等待，不会因时间到达而跳过检查或自动退出。后续启动流程还要求关节数据等条件就绪。

### 9.3 运行中的失联检测

控制程序使用主机单调时钟记录有效帧的接收时间。在控制周期读取输入前检查：

```text
当前单调时间 - 最后有效帧接收时间 ≥ imu_runtime_timeout_sec
```

默认阈值为 `0.1 s`，即 `100 ms`。达到阈值后，记录 `IMU data timeout`，锁存故障，并强制请求进入 `com.bxi.basic_actions/imu_protection` 状态。

检查随控制周期执行，实际响应时间还受调度影响。这里使用的是有效消息到达回调的时间，不使用 `header.stamp` 计算失联；第 7 节订阅示例的一秒显示阈值也不是控制器的保护阈值。

### 9.4 保护动作与恢复规则

进入 IMU 失联保护时，保护状态保存控制器当前记录的关节位置，持续生成以下关节命令：

| 命令项 | 保护状态生成的值 |
|---|---|
| 目标位置 | 进入保护时保存的关节位置，保持不变 |
| 位置增益 `kp` | 默认 `20.0` |
| 速度增益 `kd` | 默认 `1.0` |
| 目标速度 | `0` |
| 前馈力矩 | `0` |

这是固定关节位置的低刚度保持状态。锁存后，控制程序屏蔽并清空待处理的遥控状态事件，默认状态配置也没有从保护状态离开的路由。IMU 数据恢复不会自动恢复行走，按普通状态切换按键也不会解除保护。

代码预留 `release_imu_protection()` 恢复方法，默认通过 `/imu_protection_allow_release=false` 禁用。只有显式启用且有效 IMU 数据仍在超时阈值内，调用该方法才会尝试解除锁存并切换状态，默认目标为 `com.bxi.basic_actions/zero_torque`。该方法是程序内接口，当前没有对应的独立 ROS 恢复服务。

### 9.5 行走时的倾斜保护

`normal` 行走状态及继承其更新逻辑的 `forward_back` 自动前后行走状态，还会根据 IMU 姿态计算 roll 和 pitch。任意一个角度的绝对值大于 `π/3`，即 `60°`，就请求进入 `com.bxi.basic_actions/zero_torque`。

该零力矩状态生成的 `kp`、`kd` 和前馈力矩均为 `0`。倾斜保护与 IMU 失联保护的触发条件、目标状态不同；这项倾斜检查属于上述行走状态的更新逻辑，不能视为所有动作状态都具备的全局检查。

### 9.6 参数、启动与保护范围

| 配置项 | 默认值 | 用途 |
|---|---|---|
| 控制节点参数 `/imu_startup_timeout_sec` | `15.0` | 启动等待达到该时间后记录一次错误，继续等待 |
| 控制节点参数 `/imu_runtime_timeout_sec` | `0.1` | 运行中有效帧超时阈值，单位秒，必须大于零 |
| 控制节点参数 `/imu_protection_allow_release` | `false` | 是否允许程序内恢复方法解除锁存 |
| 保护状态配置 `kp`、`kd` | `20.0`、`1.0` | 保护状态生成的关节增益 |

当前 `example_demo_hw.launch.py` 提供 `imu_runtime_timeout_sec` 启动参数。例如，使用独立 IMU 数据源启动完整硬件与控制程序时：

```bash
ros2 launch bxi_example_py_elf3 example_demo_hw.launch.py \
  enable_imu:=false imu_runtime_timeout_sec:=0.1
```

该命令本身不启动独立的 `bxi_imu`，需另一个终端提供 IMU 数据，或使用已有的机器人启动流程。表中其他控制节点参数没有作为该启动文件的独立参数公开，需在控制节点参数配置中设置；保护增益位于基础动作的状态配置中。配置在初始化时读取，修改后需重启控制程序。

保护按“有效消息是否持续收到”判断，不检查消息数值是否变化，也不检查 `header.stamp` 是否陈旧或递增。重复发送旧的合法数值可能继续刷新接收时间。

当前 IMU 保护状态不会自动禁用[外部关节命令覆盖接口](mod_api_31dof_control.zh.md)，最终关节命令仍会经过覆盖逻辑。上表描述的是保护状态生成的命令，锁存状态不能理解为对所有控制输入通道的统一关闭。

## 10. CSV 记录与运行日志

启动时可控制 CSV 记录：

```bash
# 使用部署配置
ros2 launch bxi_imu imu.launch.py imu_record_enabled:=auto

# 关闭记录
ros2 launch bxi_imu imu.launch.py imu_record_enabled:=false

# 开启记录
ros2 launch bxi_imu imu.launch.py imu_record_enabled:=true
```

以上命令按需选择一条执行。记录开关不改变 ROS 消息字段。

| 项目 | 默认位置或行为 |
|---|---|
| CSV 目录 | `/var/log/bxi_log/imu/data/` |
| 遥控器启动日志目录 | `/var/log/bxi_log/imu/` |
| 文件名示例 | `imu_data_20261105_140000_0001.csv` |
| 文件生成 | 每次 IMU 进程启动生成一个文件 |
| 文件保留 | 默认保留最新十个匹配的 CSV 文件 |

CSV 包含以下数据：

| 字段 | 含义 |
|---|---|
| `receive_time_ns` | 写线程生成该行时的系统时间，单位纳秒 |
| `ros_stamp_sec`、`ros_stamp_nanosec` | 解码时填写的系统时间 |
| `quaternion_valid`、`drop_reason` | 四元数校验结果和丢弃原因 |
| `quaternion_w/x/y/z`、`quaternion_norm` | 输出方向下的四元数与模长；CSV 将 `w` 放在前面 |
| `euler_roll/pitch/yaw` | 欧拉角；零值不证明对应字段可用 |
| `angular_velocity_*`、`linear_acceleration_*` | 输出方向下的角速度与线加速度 |
| `arrival_gap_ms` | 主机记录逻辑中相邻样本的间隔 |

CSV 可以包含未通过四元数校验、没有发布到 ROS 的样本，用于排查丢帧。记录队列满或写入失败时可能缺少数据。单次运行的文件不会按大小或时长分卷。

## 11. 常见问题与排查

| 现象 | 检查方法 |
|---|---|
| 找不到 `bxi_imu` 包 | 检查是否加载了正确的 ROS 和工程环境，运行 `ros2 pkg prefix bxi_imu` |
| 有话题但没有数据 | 用 `echo --once` 等待真实消息，检查发布配置及运行日志 |
| 订阅不到已有数据 | 检查 QoS、`ROS_DOMAIN_ID`、RMW 与 DDS 网络配置 |
| 姿态或三轴方向不符合预期 | 确认 `header.frame_id`、部署的方向映射及应用是否重复变换 |
| 欧拉角、磁场等附加话题无消息 | 确认部署配置已启用对应输出，且实际数据包含这些字段 |
| 数据停留在旧值 | 记录每次回调的接收时间，检测消息是否持续更新 |
| 收到无效四元数告警 | 查看运行日志和 CSV 中的模长、有效性标记及丢弃原因 |
| 接收频率不稳定 | 检查运行日志、主机负载、通信环境和 CSV 帧间隔 |
| 控制程序一直等待 IMU | 确认收到的是通过四元数和向量有限值检查的有效帧；启动等待超时后仍会继续等待 |
| IMU 恢复后仍不能行走 | 检查是否已进入锁存的 IMU 失联保护，恢复数据不会自动解除保护 |
| 行走中切换到零力矩 | 检查 roll 或 pitch 是否超过 `60°`，并区分倾斜保护与失联保护 |
| 没有生成 CSV | 检查记录开关、目录写入权限与记录相关告警 |

建议先确认能收到 `/hardware/imu_data` 的真实消息，再核对消息字段、坐标方向和接收频率。
