---
title: 外接灵巧手
---

# 外接灵巧手

本文档面向需要在 ELF3 上快速接入 Revo2 灵巧手的客户，重点说明接线、依赖安装、编译运行和验收方法。二次开发接口、SDK 细节和完整示例代码请进入示例仓库查看：

- BXI Revo2 示例仓库：[bxi_revo2_example](https://github.com/konodoki/bxi_revo2_example)
- 灵巧手官方 SDK：[brainco-hand-sdk](https://github.com/BrainCoTech/brainco-hand-sdk.git)

!!! warning "安全提示"
    注意只有Revo2进阶版和触觉版支持58V电压，切勿把基础版接入机器人
    
    运行示例程序会驱动灵巧手执行握拳、张开、捏合、单指运动、速度/电流/PWM 控制等动作。请先确认手指活动范围内没有人体、线缆和易损物体，不要在抓取物体时直接运行完整 demo。

## 适用环境

| 项目 | 要求 |
|---|---|
| 机器人 | ELF3，已正常启动机器人硬件节点 |
| 灵巧手 | Revo2 进阶版 && 触觉版|
| 通信方式 | BXI 主控板 CANFD |
| ROS 版本 | ROS 2 Humble |
| 示例包 | `bxi_revo2_example` |
| Python SDK | `bc-stark-sdk==1.5.1` |

示例包通过 ROS 2 的 `communication/msg/CANFDPacket` 与 BXI CANFD 硬件节点通信，因此需要先加载机器人自带的 `bxi_ros2_pkg` 环境。

## 硬件连接

按默认配置接入时，不需要修改示例代码：

| 灵巧手 | BXI 主控板接口 | 默认 ID | 协议 | `master_id` |
|---|---:|---:|---|---:|
| 左手 | CAN5 | 126 / `0x7E` | CANFD | 1 |
| 右手 | CAN6 | 127 / `0x7F` | CANFD | 1 |

![Revo2 灵巧手接线示意图](../../assets/elf3/developer/dexterous_hand/dexterous_hand.jpg)

接线完成后，正常启动机器人。机器人硬件节点启动成功后，灵巧手通常会自动张开，可作为硬件链路的第一步检查。

## 快速部署

### 1. 获取示例包

在机器人主控或已配置 ROS 2 环境的开发主机上执行：

```bash
cd ~/bxi_ws
git clone https://github.com/konodoki/bxi_revo2_example.git
```

如果现场网络无法访问 GitHub，可提前下载仓库并复制到 `~/bxi_ws/bxi_revo2_example`。

### 2. 下载 C++ SDK 文件

C++ 示例编译前必须下载官方 SDK 动态库和头文件，否则会因缺少 `dist/` 目录构建失败。

```bash
cd ~/bxi_ws/bxi_revo2_example
./download-lib.sh
```

脚本会按当前系统架构下载对应文件，并生成：

- `dist/include/`
- `dist/shared/linux/libbc_stark_sdk.so`
- `VERSION`

### 3. 安装 Python SDK

如果需要运行 Python 示例，安装固定版本 SDK：

```bash
pip install bc-stark-sdk==1.5.1 --index-url https://pypi.org/simple/
```

### 4. 编译示例包

```bash
cd ~/bxi_ws/bxi_revo2_example
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
colcon build
source install/setup.bash
```

!!! tip "提示"
    如果 `communication` 消息包位于其他工作空间，请先 `source` 对应工作空间的 `install/setup.bash`，再执行 `colcon build`。

## 启动与验收

### 1. 设置 CANFD 通信环境

灵巧手示例通过 `/canfd_packet/rx` 和 `/canfd_packet/tx` 与机器人硬件节点通信。由于硬件节点通常在 root 用户下运行，必须在 root shell 中设置相同的 ROS 2 Domain 和 CycloneDDS 网络配置，并在同一个 shell 中启动示例程序：

```bash
sudo su
export ROS_DOMAIN_ID=机器人的DOMAIN_ID
export RMW_IMPLEMENTATION=rmw_cyclonedds_cpp
export ROS_LOCALHOST_ONLY=0
export CYCLONEDDS_URI='<CycloneDDS><Domain Id="any"><General><Interfaces><NetworkInterface name="lo" multicast="true"/></Interfaces><AllowMulticast>true</AllowMulticast></General></Domain></CycloneDDS>'
```

将 `机器人的DOMAIN_ID` 替换为机器人实际使用的数字。不要只在普通用户终端设置这些变量后再切换到 root；`sudo su` 不会自动继承所有 ROS 环境变量。

### 2. 启动机器人硬件节点

先按 ELF3 正常流程启动机器人。可参考[运动控制开发指南](motioncontrol.md#启动机器人程序)中的启动方式。

启动后检查 CANFD 通信话题是否存在：

```bash
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
ros2 topic list | grep canfd_packet
```

正常情况下应能看到类似话题：

```text
/canfd_packet/rx
/canfd_packet/tx
```

### 3. 运行示例程序

运行 C++ 示例：

```bash
cd ~/bxi_ws/bxi_revo2_example
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
ros2 run bxi_revo2_example bxi_revo2_example
```

或运行 Python 示例：

```bash
cd ~/bxi_ws/bxi_revo2_example
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source install/setup.bash
ros2 run bxi_revo2_example bxi_revo2_example.py
```

### 3. 验收现象

程序运行后，终端会打印设备信息、手指位置、速度、电流和配置参数。灵巧手会依次执行：

1. 基本位置控制：握拳、张开、单指移动；
2. 速度、电流、PWM 控制；
3. Revo2 高级控制：单位模式、位置+时间、位置+速度、多指联动；
4. 内置动作序列：Open、Fist、Pinch、Point 等；
5. 设备信息和参数查询。

默认程序会先运行左手，再运行右手。两只手均能完成上述动作且终端无持续报错，即表示基础部署完成。

## 修改默认接线或 ID

如果现场接线不是默认的 CAN5/CAN6，或灵巧手 ID 被修改过，需要在示例代码中同步修改总线和 ID。

Python 示例位置：

```text
~/bxi_ws/bxi_revo2_example/src/bxi_revo2_example.py
```

默认配置：

```python
left_ctx = await init_bxipci_device(5, 126, master_id=1, is_canfd=True, ...)
right_ctx = await init_bxipci_device(6, 127, master_id=1, is_canfd=True, ...)
```

C++ 示例位置：

```text
~/bxi_ws/bxi_revo2_example/src/bxi_revo2_example.cpp
```

默认配置：

```cpp
init_bxipci_device(&left_ctx_, 5, 126, true);
init_bxipci_device(&right_ctx_, 6, 127, true);
```

修改后重新编译并加载环境：

```bash
cd ~/bxi_ws/bxi_revo2_example
colcon build
source install/setup.bash
```

## 常见问题

### 编译时报缺少 `stark-sdk.h` 或 `libbc_stark_sdk.so`

未下载 C++ SDK。进入示例包目录执行：

```bash
./download-lib.sh
```

然后重新编译。

### Python 运行时报 `No module named bc_stark_sdk`

Python SDK 未安装或安装到错误的 Python 环境。执行：

```bash
pip install bc-stark-sdk==1.5.1 --index-url https://pypi.org/simple/
```

### 运行时报 `communication.msg.CANFDPacket not found`

未加载 BXI ROS 2 消息包环境。执行：

```bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
source ~/bxi_ws/bxi_revo2_example/install/setup.bash
```

### 灵巧手无响应或读取超时

按以下顺序检查：

1. 左手是否接在 CAN5，ID 是否为 126；
2. 右手是否接在 CAN6，ID 是否为 127；
3. 机器人硬件节点是否已启动，`/canfd_packet/rx` 和 `/canfd_packet/tx` 是否存在；
4. 线缆和供电是否正常；
5. 是否有其他程序正在同时控制同一只灵巧手。
6. 若为出厂自带硬件节点请检查ROS_DOMAIN_ID是否一致

## 二次开发入口

客户部署时通常不需要修改底层通信桥接代码。若需要在自己的 ROS 2 节点中控制灵巧手，请参考示例仓库 README 中的 “在自己的 ROS 2 Node class 中使用” 章节：

[https://github.com/konodoki/bxi_revo2_example](https://github.com/konodoki/bxi_revo2_example)
