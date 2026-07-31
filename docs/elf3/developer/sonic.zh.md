---
title: Sonic 全身遥操
---

# Sonic 全身遥操

本文档介绍如何在 ELF3 上部署和使用 Sonic 全身遥操功能，包括机器人端依赖安装、PICO 体感追踪器校准、XRoboToolkit 网络配置，以及全身动作跟随和退出流程。

- 运动控制仓库：[bxi_rl_controller_ros2_example](https://github.com/bxirobotics/bxi_rl_controller_ros2_example)
- PICO 客户端：[XRoboToolkit-PICO-1.1.1.apk](https://github.com/XR-Robotics/XRoboToolkit-Unity-Client/releases/download/v1.1.1/XRoboToolkit-PICO-1.1.1.apk)

!!! warning "安全提示"
    全身遥操会同时驱动机器人的腿部、躯干和双臂，操作不当可能导致机器人失稳或与周围人员、物体发生碰撞。首次使用前应清空机器人和操作者周围的活动区域，确认急停装置可用，并安排人员在机器人旁保护。

    操作者应从幅度小、速度慢的动作开始，避免跳跃、快速转身、单脚站立以及超过机器人关节活动范围的动作。机器人出现抖动、姿态异常或失稳趋势时，应立即停止跟随；必要时按下急停按钮。

## 适用环境

| 项目 | 要求 |
|---|---|
| 机器人 | ELF3，已正常启动运动控制程序 |
| 机器人端工程 | `/home/bxi/bxi_ws/bxi_rl_controller_ros2_example` |
| 输入设备 | 机器人遥控器、PICO 头显及左右手柄 |
| 体感设备 | 2 个腿部体感追踪器 |
| PICO 应用 | XRoboToolkit-PICO 1.1.1 |
| 网络 | PICO 与机器人位于同一局域网，且可相互通信 |

## 机器人端准备

### 1. 更新运动控制工程

将机器人上的 `bxi_rl_controller_ros2_example` 更新到最新版本：

```bash
cd /home/bxi/bxi_ws/bxi_rl_controller_ros2_example
git pull --ff-only
```

更新代码后，按照仓库 README 重新编译工程并加载环境：

```bash
source /opt/ros/humble/setup.bash
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd /home/bxi/bxi_ws/bxi_rl_controller_ros2_example
bash build.sh
source install/setup.bash
```

!!! tip "提示"
    如果现场版本通过其他方式统一部署，请使用对应的更新和编译流程。不要在工作区存在未提交修改时直接执行更新，以免覆盖现场配置。

### 2. 安装 Sonic 依赖

首次使用 Sonic 时，在机器人端进入 root 用户并安装 PICO 接入所需的 Python 依赖：

```bash
sudo su
python3 -m pip install -r /home/bxi/bxi_ws/bxi_rl_controller_ros2_example/src/bxi_example_py_elf3/mods/com.bxi.sonic/requirements-pico.txt
```

依赖只需安装一次；更新工程后如果 `requirements-pico.txt` 发生变化，应重新执行该命令。

### 3. 安装 PICO 应用

下载 [XRoboToolkit-PICO-1.1.1.apk](https://github.com/XR-Robotics/XRoboToolkit-Unity-Client/releases/download/v1.1.1/XRoboToolkit-PICO-1.1.1.apk)，并将 APK 安装到 PICO 头显。安装完成后，可在 PICO 资源库的 **未知来源** 中找到 `XRoboToolkit`。

## 进入 Sonic 就绪状态

1. 正常启动 ELF3，确认机器人已完成自检，并使用遥控器让机器人进入行走模式。此时机器人应保持正常站立姿态。

   ![ELF3 处于正常站立状态](../../assets/elf3/developer/sonic/normal_state.jpg)

2. 同时按下遥控器的 `LB + RB + X`，请求进入 Sonic 全身遥操状态。

3. 等待机器人完成状态切换。进入 Sonic 就绪状态后，机器人会切换到下图所示姿态；机器人姿态稳定后，再开始 PICO 校准和动作跟随。

   ![ELF3 进入 Sonic 全身遥操就绪状态](../../assets/elf3/developer/sonic/sonic_state.jpg)

!!! note "没有进入 Sonic 状态"
    请先确认机器人已经处于正常行走模式，再同时按下 `LB + RB + X`。如果仍无响应，请检查运动控制工程是否已更新、重新编译并正确加载。

## 校准 PICO 体感追踪器

每次开始全身遥操前都建议重新校准体感追踪器，以减少人体姿态和地面高度偏差。

1. 将两个体感追踪器分别固定在左右腿上。追踪器的按钮和指示灯一侧应朝向身体上方，然后按下按钮开启追踪器。

2. 戴好 PICO 头显并拿起左右手柄。在 PICO 主界面点击右下角的 **体感追踪器**。

   ![在 PICO 主界面打开体感追踪器](../../assets/elf3/developer/sonic/pico_screen1.png)

3. 确认两个腿部追踪器均已连接，然后点击 **开始校准**，按照头显中的引导完成校准动作。

   ![确认追踪器连接并开始校准](../../assets/elf3/developer/sonic/pico_screen2.png)

4. 校准完成后，点击 **调整地面**，按照提示将虚拟地面调整到实际地面位置。

   ![调整 PICO 体感追踪的地面高度](../../assets/elf3/developer/sonic/pico_screen3.png)

5. 观察界面中的虚拟人物。操作者活动头部、双手和双腿时，虚拟人物应同步变化，且双脚应基本贴合地面。

   ![确认虚拟人物与操作者动作同步](../../assets/elf3/developer/sonic/pico_screen4.png)

## 连接 XRoboToolkit

1. 返回 PICO 资源库，在 **未知来源** 中打开 `XRoboToolkit`。

   ![在未知来源中打开 XRoboToolkit](../../assets/elf3/developer/sonic/pico_screen5.png)

2. 确认 PICO 与机器人连接到同一局域网，并获取机器人的局域网 IP 地址。

3. 在 XRoboToolkit 的 **Network** 区域点击 `PC Service` 右侧的 **Enter**，输入机器人的 IP 地址并连接。

4. 按下表检查追踪和发送选项：

   | 区域 | 选项 | 设置 |
   |---|---|---|
   | Tracking | `Head` | 勾选 |
   | Tracking | `Controller` | 勾选 |
   | PICO Motion Tracker | `Mode` | 选择 `Full-body` |
   | PICO Motion Tracker | `High-Acc` | 勾选 |
   | PICO Motion Tracker | `Num` | 设置为 `2` |
   | Data & Control | `Send` | 勾选 |

5. 确认 **Network** 区域的 `Status` 显示为 `WORKING`，日志中没有持续报错。

   ![配置 XRoboToolkit 全身追踪和数据发送](../../assets/elf3/developer/sonic/pico_screen6.png)

## 校准姿态并开始跟随

1. 操作者面向与机器人一致的方向，全身保持直立。双臂自然下垂，肘关节弯曲约 90°，前臂水平向前，使身体和双臂呈下图所示姿态。

   ![Sonic 全身遥操初始校准姿态](../../assets/elf3/developer/sonic/inital_pose.png)

2. 保持姿态稳定，同时按下左右 PICO 手柄上的 `A + B + X + Y` 四个按键，完成 PICO 三点追踪与机器人参考姿态的对齐。

3. 校准完成后，继续保持与机器人姿态和朝向一致，确认头显中的人体追踪没有明显漂移。

4. 同时按下 PICO 手柄的 `A + X`，机器人开始跟随操作者的全身动作。开始跟随后先缓慢移动双臂，再小幅移动身体和双腿，确认动作方向正确。

5. 需要暂停跟随并恢复默认姿态时，再次同时按下 `A + X`。

6. 确认机器人已经停止实时跟随后，同时按下机器人遥控器的 `RB + X`，使机器人返回正常行走模式。

常用按键如下：

| 设备 | 按键 | 功能 |
|---|---|---|
| 机器人遥控器 | `LB + RB + X` | 从行走模式进入 Sonic 就绪状态 |
| PICO 左右手柄 | `A + B + X + Y` | 校准人体追踪与机器人参考姿态 |
| PICO 左右手柄 | `A + X` | 开始跟随；再次按下时恢复默认姿态 |
| 机器人遥控器 | `X` | 在未按肩键或扳机键时重置朝向对齐 |
| 机器人遥控器 | `RB + X` | 退出 Sonic 并返回正常行走模式 |

## 验收检查

完成部署后，应能观察到以下现象：

1. PICO 体感追踪器界面中，两个腿部追踪器均显示已连接；
2. 虚拟人物的头部、双手和双腿能够与操作者同步运动；
3. XRoboToolkit 的状态显示为 `WORKING`，`Mode` 为 `Full-body`，且 `Send` 已勾选；
4. 按下 `LB + RB + X` 后，机器人能够稳定进入 Sonic 就绪姿态；
5. 完成 `A + B + X + Y` 校准并按下 `A + X` 后，机器人能够低延迟地跟随小幅动作；
6. 再次按下 `A + X` 后机器人恢复默认姿态，按下 `RB + X` 后能够返回正常行走模式。

## 常见问题

### XRoboToolkit 无法连接机器人

- 确认 PICO 与机器人位于同一局域网；
- 确认 `PC Service` 中填写的是机器人 IP，而不是 PICO IP；
- 检查 IP 地址是否因网络切换发生变化；
- 确认 XRoboToolkit 状态为 `WORKING`，并查看日志中的连接错误。

### 虚拟人物的腿部不跟随或脚底悬空

- 检查两个腿部追踪器是否均已连接且电量充足；
- 确认追踪器的按钮和指示灯一侧朝向身体上方；
- 重新执行 **开始校准** 和 **调整地面**；
- 确认 XRoboToolkit 中 `Mode` 为 `Full-body`、`Num` 为 `2`。

### 机器人无法进入 Sonic 就绪状态

- 确认机器人已经完成自检并处于正常行走模式；
- 确认按下的是 `LB + RB + X` 三键组合；
- 确认工程已更新到最新版本并重新编译；
- 首次使用时，确认 `requirements-pico.txt` 中的依赖已安装到机器人实际运行使用的 Python 环境。

### 完成校准后机器人不跟随

- 确认 XRoboToolkit 的 `Send` 已勾选且状态为 `WORKING`；
- 确认 PICO 体感追踪界面的虚拟人物可以正常跟随；
- 保持初始姿态，重新按下 `A + B + X + Y`；
- 等待校准完成后，再按下 `A + X` 开始实时跟随。

### 机器人动作方向与操作者不一致

先停止实时跟随，让操作者与机器人面向同一方向并重新校准。若仅朝向存在偏差，可在未按下肩键或扳机键时，单独按机器人遥控器的 `X` 重置朝向对齐。

### 跟随过程中出现卡顿或姿态跳变

停止大幅动作，并检查 PICO 与机器人的无线网络质量、追踪器连接状态和 XRoboToolkit 日志。恢复跟随前应重新确认初始姿态和周围安全；问题持续存在时，退出 Sonic 状态后重新校准和连接。

## 参考资料

- [bxi_rl_controller_ros2_example](https://github.com/bxirobotics/bxi_rl_controller_ros2_example)
- [Sonic ELF3 部署与验收说明](https://github.com/bxirobotics/bxi_rl_controller_ros2_example/blob/main/src/bxi_example_py_elf3/mods/com.bxi.sonic/SONIC_ELF3.md)
- [XRoboToolkit Unity Client](https://github.com/XR-Robotics/XRoboToolkit-Unity-Client)
