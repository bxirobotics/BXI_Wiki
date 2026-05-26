---
title: 半身遥操
---

# 半身遥操

本文档面向需要快速部署 ELF3 半身遥操功能的客户，重点说明 Pico 4 Ultra、图传、仿真验证、真机启动和现场操作流程。算法、节点实现、遥控器扩展和更多开发说明请进入示例仓库查看：

- 半身遥操示例仓库：[bxi_teleop_v2](https://github.com/konodoki/bxi_teleop_v2)

!!! warning "安全提示"
    当前示例的下半身 locomotion 模型不直接输出手臂关节控制量，手臂关节由 Pico 手柄姿态经 IK 解算后拼接到控制链路。真机运行时存在站立稳定性风险，必须先完成仿真验证；真机测试时请安排人员在旁保护，并确保急停装置可用。

## 功能说明

半身遥操示例集成以下功能：

- ELF3 强化学习运动控制示例；
- Mujoco 仿真和真机启动入口；
- 手柄或键盘遥控；
- Pico 4 Ultra 头显图传；
- Pico 手柄姿态到 ELF3 双臂 IK 的遥操作控制；
- 可选的手部动作录制。

仓库内的 `BxiPicoApp-release.apk` 目前仅在 Pico 4 Ultra 平台完成测试。默认部署使用 `elf3_arm_bringup_nohand.launch.py`，不会启动灵巧手外部驱动。

## 适用环境

| 项目 | 要求 |
|---|---|
| 机器人 | ELF3 |
| 操作系统 | Ubuntu 22.04 |
| ROS 版本 | ROS 2 Humble |
| 基础包 | `/opt/bxi/bxi_ros2_pkg`，提供 `communication`、`mujoco`、`hardware_elf3` 等依赖 |
| 头显 | Pico 4 Ultra |
| 摄像头 | USB 摄像头，默认设备号 `/dev/video4` |
| 图传端口 | MediaMTX RTSP `2212` |
| 示例仓库 | `bxi_teleop_v2` |

## 快速部署

### 1. 获取示例工程

在机器人主控或已配置 ROS 2 环境的开发主机上执行：

```bash
cd ~/bxi_ws
git clone https://github.com/konodoki/bxi_teleop_v2.git
cd bxi_teleop_v2
```

如果现场网络无法访问 GitHub，可提前下载仓库并复制到 `~/bxi_ws/bxi_teleop_v2`。

### 2. 安装依赖

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

### 3. 编译工程

```bash
cd ~/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
bash build.sh
source install/setup.bash
```

!!! tip "提示"
    真机环境下，硬件相关命令建议在 root 用户中执行，并在 root 终端内重新加载 ROS 2、BXI 基础包和本工程的 `install/setup.bash`。

## Pico 图传检查

### 1. 准备 Pico 和摄像头

1. 将仓库根目录中的 `BxiPicoApp-release.apk` 安装到 Pico 4 Ultra；
2. 确保 Pico 和运行本工程的电脑处于同一局域网；
3. 将摄像头接入电脑 USB 3.0 口；
4. 当前代码默认读取 `/dev/video4`。

### 2. 启动 Pico 接入和图传服务

```bash
cd ~/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

若出现类似日志，表示摄像头已成功推流：

```text
[pico_bxi_server-1] INF [RTSP] [session ...] is publishing to path 'video', 1 track (H264)
```

Pico 应用会扫描局域网内开放 `2212` 端口的设备，并列出可能的 RTSP 服务 IP。使用 Pico 手柄选择对应 IP 后，即可接入图传画面。需要关闭图传画面时，按右手手柄 `A` 键进入透传模式。

也可以单独测试推流：

```bash
cd ~/bxi_ws/bxi_teleop_v2
bash push_rtsp.sh
```

## 仿真验证

真机运行前必须先完成仿真验证。建议打开 3 个终端，每个终端均先执行：

```bash
cd ~/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
```

终端 1：启动遥控器。默认使用手柄输入：

```bash
ros2 launch remote_controller remote_controller.launch.py
```

没有手柄时，可使用键盘输入：

```bash
ros2 launch remote_controller remote_controller_keyboard.launch.py
```

终端 2：启动 Pico、双臂 IK 和图传服务：

```bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

终端 3：启动 Mujoco 仿真和控制策略：

```bash
ros2 launch bxi_example_py_elf3 example_demo.launch.py
```

!!! warning "注意"
    `example_demo.launch.py` 会同时启动仿真和控制程序。启动后不要再次按下遥控器上的启动按键，避免重复触发启动流程。

## 真机启动

真机操作风险较高。启动前请确认急停、供电、网络、工作空间和周围环境均处于安全状态。

真机环境建议先进入 root 用户：

```bash
sudo su
cd /home/bxi/bxi_ws/bxi_teleop_v2
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
```

同样建议打开 3 个 root 终端。

终端 1：启动遥控器：

```bash
ros2 launch remote_controller remote_controller.launch.py
```

终端 2：启动 Pico、双臂 IK 和图传服务：

```bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

终端 3：启动真机硬件节点和控制策略：

```bash
ros2 launch bxi_example_py_elf3 example_demo_hw.launch.py
```

如果提示已有硬件控制实例正在运行，请先确认并停止旧实例。`example_demo_hw.launch.py` 会使用 `/tmp/bxi_example_hw.lock` 锁文件避免重复启动。

## 校准与遥操流程

1. 启动 `elf3_arm_ikpy_control_pico` 后，将双手举过头顶；
2. 节点提示开始校准后，以两侧肩关节为圆心，尽量伸直双臂并覆盖完整球面轨迹；
3. 终端显示校准成功后，进入下一步；
4. 使用遥控器让机器人进入 `normal` 站立状态；
5. 按下 `RT + A` 进入遥操状态；
6. 握紧 Pico 手柄抓握键后，对应侧手臂开始跟随 Pico 手柄运动；
7. 两个扳机同时按紧时开始手部动作录制，任意一个扳机松开后结束录制。

录制文件默认保存到：

```text
install/bxi_example_py_elf3/share/bxi_example_py_elf3/data/teleop_records
```

## 验收现象

基础部署完成后，应能观察到：

1. Pico 应用可发现 `2212` 端口的图传服务 IP，并显示摄像头画面；
2. `elf3_arm_bringup_nohand.launch.py` 终端持续输出 Pico 连接或 RTSP 推流日志；
3. 仿真中机器人可进入站立和遥操流程；
4. 握紧 Pico 抓握键后，仿真或真机双臂跟随 Pico 手柄运动；
5. 真机运行过程中无持续丢包、保护触发或控制节点异常退出。

## 常见问题

### 找不到 `communication`、`mujoco` 或 `hardware_elf3`

通常是未正确加载 BXI ROS 2 基础包：

```bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
```

然后重新构建或启动。

### Pico 端找不到图传 IP

请检查：

1. Pico 和电脑是否位于同一局域网；
2. 电脑防火墙是否拦截 `2212` 端口；
3. MediaMTX 是否正在监听端口：

```bash
ss -lntup | grep 2212
```

### 摄像头无法打开

当前代码默认使用 `/dev/video4`。如果实际设备号不同，请修改：

```text
src/pico_bxi_server/src/pico_bxi_server.cpp
push_rtsp.sh
```

也请确认摄像头已接入 USB 3.0 口，且当前用户具备摄像头访问权限。临时调试可执行：

```bash
sudo chmod 777 /dev/video4
```

### 启动完整 bringup 后找不到 `aero_hand_open`

当前仓库未包含 `aero_hand_open` 实现。未额外安装灵巧手驱动时，请使用：

```bash
ros2 launch elf3_arm_bringup elf3_arm_bringup_nohand.launch.py
```

### 真机节点无法互相发现

请确认机器人和运行遥操工程的终端使用相同的 `ROS_DOMAIN_ID`。修改后需要重新启动相关 ROS 2 节点。

## 二次开发入口

客户快速部署时通常不需要修改底层图传、Pico 数据接入或 IK 节点。若需要扩展遥控器输入、修改状态机、替换模型或接入灵巧手，请参考示例仓库 README：

[https://github.com/konodoki/bxi_teleop_v2](https://github.com/konodoki/bxi_teleop_v2)
