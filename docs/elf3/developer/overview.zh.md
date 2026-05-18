---
title: 系统设置说明
---

# 控制系统架构

半醒提供全栈开放架构： 
    
- 基于CANFD的电机硬件控制|调试接口；     
- 基于Mujoco的仿真环境、机器人URDF/xml等；     
- 基于ROS2的硬件管理节点，控制策略无缝部署到仿真/真机硬件；     
- 基于强化学习的运控控制训练示例代码；    

![系统架构](../../assets/elf3/developer/overview/software_structure.png) 

## CAN 总线与 CAN ID

机器人全身共有 **31 个关节电机**，分布在 **5 路 CANFD 总线**上。每路总线对应一个身体部位：

| CAN 总线 | 接口名称 | 对应部位 | 电机数量 |
|---|---|---|---|
| 0 | CANFD_0 | 腰部 / 颈部 Waist & Neck | 5 |
| 1 | CANFD_1 | 左腿 L_leg | 6 |
| 2 | CANFD_2 | 右腿 R_leg | 6 |
| 3 | CANFD_3 | 左臂 L_arm | 7 |
| 4 | CANFD_4 | 右臂 R_arm | 7 |

下图为机器人 URDF 可视化模型，图上标注了各关节索引：

> 【补充：此处待插入标注关节索引的 URDF 可视化图片】

下表给出每个电机的关节索引、关节名称、CAN 总线与 CAN ID。其中：

- **关节索引**即控制程序中关节/电机数组的索引，从 `0` 开始全身连续编号；
- **CAN ID** 为电机在所属总线上的地址，在**每条总线内独立从 `1` 开始递增**。

| 关节索引 | 关节名称 | CAN 总线 | CAN ID |
|---|---|---|---|
| 0 | waist_y_joint | 0 | 1 |
| 1 | waist_x_joint | 0 | 2 |
| 2 | waist_z_joint | 0 | 3 |
| 3 | l_hip_y_joint | 1 | 1 |
| 4 | l_hip_x_joint | 1 | 2 |
| 5 | l_hip_z_joint | 1 | 3 |
| 6 | l_knee_y_joint | 1 | 4 |
| 7 | l_ankle_y_joint | 1 | 5 |
| 8 | l_ankle_x_joint | 1 | 6 |
| 9 | r_hip_y_joint | 2 | 1 |
| 10 | r_hip_x_joint | 2 | 2 |
| 11 | r_hip_z_joint | 2 | 3 |
| 12 | r_knee_y_joint | 2 | 4 |
| 13 | r_ankle_y_joint | 2 | 5 |
| 14 | r_ankle_x_joint | 2 | 6 |
| 15 | l_shoulder_y_joint | 3 | 1 |
| 16 | l_shoulder_x_joint | 3 | 2 |
| 17 | l_shoulder_z_joint | 3 | 3 |
| 18 | l_elbow_y_joint | 3 | 4 |
| 19 | l_wrist_x_joint | 3 | 5 |
| 20 | l_wrist_y_joint | 3 | 6 |
| 21 | l_wrist_z_joint | 3 | 7 |
| 22 | r_shoulder_y_joint | 4 | 1 |
| 23 | r_shoulder_x_joint | 4 | 2 |
| 24 | r_shoulder_z_joint | 4 | 3 |
| 25 | r_elbow_y_joint | 4 | 4 |
| 26 | r_wrist_x_joint | 4 | 5 |
| 27 | r_wrist_y_joint | 4 | 6 |
| 28 | r_wrist_z_joint | 4 | 7 |
| 29 | neck_z_joint | 0 | 4 |
| 30 | neck_y_joint | 0 | 5 |

## Domain ID

### 作用

机器人控制系统基于 ROS2 构建，ROS2 底层采用 DDS 进行节点通信。**`ROS_DOMAIN_ID`** 用于划分通信域：

- 处于**相同** Domain ID 的节点可以相互发现并收发话题/服务；
- 处于**不同** Domain ID 的节点彼此隔离，互不干扰。

当同一局域网内存在多台机器人，或同时连接多台调试主机时，如果它们使用相同的 Domain ID，话题数据会相互串扰，导致控制异常。**为每台机器人分配独立的 Domain ID，即可将各机器人的 ROS2 通信网络相互隔离。**

### 默认 Domain ID

机器人出厂已按以下规则配置默认 Domain ID，启动方式不同取值不同：

- **手柄启动**：`ROS_DOMAIN_ID = 机器人代数 × 10 + 机器人序号`。
  ELF3 为第三代产品，代数为 `3`，因此 Domain ID 为 `30 + 序号`。
    - 例：`elf3-15` → `3 × 10 + 15 = 45`
    - 例：`elf3-20` → `3 × 10 + 20 = 50`
- **APP 启动**：`ROS_DOMAIN_ID` 固定为 `22`。

### 设置方法

Domain ID 通过环境变量设置。在机器人主机或开发主机的终端中执行：

```bash
export ROS_DOMAIN_ID=45
```

如需开机自动生效，可将上述命令写入 `~/.bashrc`：

```bash
echo "export ROS_DOMAIN_ID=45" >> ~/.bashrc
source ~/.bashrc
```

!!! tip "提示"
    - `ROS_DOMAIN_ID` 取值建议范围为 `0–101`。
    - 上位机（开发主机）需与目标机器人设置**相同**的 Domain ID 才能与其通信。
    - 修改后需重新启动相关 ROS2 节点才能生效。

## 文档目录

- 基于ROS2的控制策略部署框架，无缝部署到仿真/真机硬件：https://github.com/bxirobotics/bxi_rl_controller_ros2_example    
- 机器人URDF：https://github.com/bxirobotics/bxi_rl_controller_ros2_example/tree/main/resources    
