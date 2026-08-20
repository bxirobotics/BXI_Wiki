---
title: 半身遥操
---

# 半身遥操

`com.bxi.upper_body_teleop` 是独立的 ELF3 Mod，自带 PICO 接入、MediaMTX、头部相机 RTSP、Pinocchio 双臂 IK 和运行库，仅依赖 `com.bxi.basic_actions`。不需要旧版 `bxi_teleop_v2` 或额外的 bringup 节点。

- Mod：[com.bxi.upper_body_teleop](https://github.com/konodoki/com.bxi.upper_body_teleop)
- PICO 客户端：[XRoboToolkit-PICO-1.1.1.apk](https://github.com/XR-Robotics/XRoboToolkit-Unity-Client/releases/download/v1.1.1/XRoboToolkit-PICO-1.1.1.apk)

!!! warning "安全提示"
    真机运行前必须完成仿真验证，使用吊架或其他保护措施，清空双臂运动范围并保持急停可达。首次操作从小幅、低速动作开始。

## 安装

将 Mod 安装到不会被 App 更新覆盖的独立目录：

```bash
sudo mkdir -p /opt/bxi/mods
sudo git clone https://github.com/konodoki/com.bxi.upper_body_teleop.git /opt/bxi/mods/com.bxi.upper_body_teleop
```

更新已有仓库：

```bash
cd /opt/bxi/mods/com.bxi.upper_body_teleop
git pull --ff-only
```

旧项目若在内置 `mods` 或 `private_git_mods` 中已有同一个 Mod，必须备份并移出扫描目录，否则会因重复 Mod ID 拒绝启动。

## 启动

| 启动方式 | 工程目录 | 说明 |
|---|---|---|
| 手柄启动 | `~/bxi_ws/bxi_rl_controller_ros2_example` | 源码目录；更新主工程后重新编译，Mod 从 `/opt/bxi/mods` 加载。 |
| App 启动 | `/opt/bxi/bxi_rl_controller_ros2_example` | App 自动下载的预编译目录，不需手动编译，Mod 从 `/opt/bxi/mods` 加载。 |

正常启动机器人和控制程序后，进入 `com.bxi.upper_body_teleop/upper_body_teleop` 状态时，Mod 节点会自动启动。不要再运行旧版 `elf3_arm_bringup_nohand.launch.py`、`pico_bxi_server` 或 `bxi_teleop_v2` 脚本。

## PICO 连接与校准

PICO 的连接和体感校准流程与 Sonic 相同：

1. 将两个体感追踪器分别固定在左右腿上，按钮和指示灯一侧朝上并开机。
2. 在 PICO 主界面打开 **体感追踪器**，确认两个追踪器已连接，点击 **开始校准** 并完成引导。
3. 校准完成后点击 **调整地面**，将虚拟地面对齐实际地面。
4. 打开 `XRoboToolkit`，在 **Network → PC Service** 中输入机器人的局域网 IP 并连接。
5. 确认以下选项：

   | 区域 | 选项 | 设置 |
   |---|---|---|
   | Tracking | `Head` | 勾选 |
   | Tracking | `Controller` | 勾选 |
   | PICO Motion Tracker | `Mode` | `Full-body` |
   | PICO Motion Tracker | `High-Acc` | 勾选 |
   | PICO Motion Tracker | `Num` | `2` |
   | Data & Control | `Send` | 勾选 |

6. 确认 `Network` 状态为 `WORKING`，并且日志没有持续报错。之后再进入 Mod 状态并执行按键校准。

## 操作

1. 在 `normal` 状态按遥控器 `LB + LT + X`（`btn_10=17`）进入半身遥操。
2. PICO 开启 Body Tracking、Controller 和 Send，确认 XRoboToolkit 状态为 `WORKING`。
3. 保持标准站姿，同时按 `A+B+X+Y` 校准；成功后自动进入 POSE，不需要按 `A+X`。
4. 握紧左/右 grip 后，对应手臂开始跟随；松开 grip 后平滑回到 PD 站立姿态。
5. 左右 trigger 控制对应夹爪。每次进入状态后夹爪会先进行低速限位校准。
6. 需要重新校准时再次按 `A+B+X+Y`；校准期间双臂回到 PD 姿态。
7. 退出使用系统标准事件返回 `normal`、`PD brake`、`recover` 或 `zero-torque`。

`A+X` 在当前 Mod 中不再切换跟随模式。PICO 暂时断连时，下半身继续由步态策略控制，双臂保持 PD 姿态。

## 图传

MediaMTX 和头部相机节点由 Mod 自动管理，默认地址为 `rtsp://<机器人IP>:2212/video`。PICO 应用在局域网中选择该地址即可，不需要单独运行图传脚本。

## 验收与故障排查

- 日志应显示 `mediamtx_server`、`head_camera_rtsp`、`pico_manager` 和 `arm_ik_bridge` 自动启动；
- `A+B+X+Y` 后自动进入 POSE，握 grip 时对应手臂跟随；
- trigger 能控制对应夹爪，退出状态后子节点自动停止。

若提示重复 Mod ID，只保留 `/opt/bxi/mods/com.bxi.upper_body_teleop`，移出工程内旧副本。若没有 PICO 数据，唤醒头显、开启 Body Tracking 和 Send，并确认状态为 `WORKING`。
