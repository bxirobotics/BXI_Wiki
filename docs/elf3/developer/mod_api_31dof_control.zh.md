# 最简控制 ELF3 的 31 自由度

本文提供两种关节控制方式：只控制头部时，直接向 `actuators_cmds_override` 发布具名关节命令，不需要写代码；需要完整控制 31 自由度时，再创建一个只有 `state.py` 和 `mod.yaml` 的 Mod，在 `on_update()` 中直接生成轨迹。

示例基于 Mod API 4.0：

- [完整框架代码](https://github.com/bxirobotics/bxi_rl_controller_ros2_example.git)
- [Mod API 完整文档](https://github.com/bxirobotics/bxi_rl_controller_ros2_example/wiki)

以下命令默认在框架代码仓库根目录执行。

## 运行前确认：真机默认是 29 自由度

真机硬件 launch 默认使用 `enable_head:=auto`，并从 `/opt/bxi/robot_config.yaml` 读取机器人模块配置。只有同时满足以下条件，才会启用两个头部关节并启动完整的 31 自由度硬件：

1. `/opt/bxi/robot_config.yaml` 文件存在且能够正常读取；
2. 配置中包含 `modules.head.enabled: true`。

最小配置结构如下。正式配置应使用 `bxi_robot_config_tool` 生成：

```yaml
modules:
  head:
    enabled: true
```

以下任一情况都会使用内置默认值，启动不含头部电机的 29 自由度模式：

- `/opt/bxi/robot_config.yaml` 不存在、不可读或内容格式错误；
- 配置中没有 `modules.head.enabled`；
- `modules.head.enabled` 为 `false`。

当前实现无论是否启用头部都使用同一个 `hardware_elf3` 包。启动日志中的
`motor_disable` 掩码可以确认头部电机是否启用：

```text
# 启用头部；未叠加其他电机禁用位时
[bxi hardware config] package=hardware_elf3, motor_disable=0x00000000, ...

# 禁用头部；未叠加其他电机禁用位时
[bxi hardware config] package=hardware_elf3, motor_disable=0x60000000, ...
```

如果配置还禁用了其他电机，`motor_disable` 可能不是上面的完整示例值。判断头部状态时
只检查对应掩码：`motor_disable & 0x60000000 == 0` 表示头部启用，
`motor_disable & 0x60000000 == 0x60000000` 表示头部禁用。不要再根据
`hardware_elf3_head` 与 `hardware_elf3` 的包名区别判断自由度模式。

29 自由度模式下，运行时关节布局中没有 `head_z_joint` 和 `head_y_joint`，因此下面的头部覆盖命令会因关节名未知而被拒绝。需要先生成正确的 `/opt/bxi/robot_config.yaml`，再重新启动真机程序。仿真使用的 ELF3 模型本身包含两个头部关节，不受这项真机硬件配置限制。

!!! note "手动覆盖仅用于调试"
    硬件 launch 也支持 `enable_head:=true` 或 `enable_head:=false` 强制覆盖自动判定，但标准部署应以 `/opt/bxi/robot_config.yaml` 为准，避免软件配置与实际硬件不一致。

!!! danger "先在仿真中验证并选择正确的测试方式"
    关节覆盖和自定义 Mod 都会直接生成电机命令。真机测试前必须清空周围人员和障碍物、准备急停，并先使用小角度和较低增益验证关节方向。

    机器人落地承重时，如需覆盖手臂或手部关节，必须先进入不依赖手臂维持平衡的模型，例如 `com.bxi.basic_actions/hello`（挥手）或 `com.bxi.basic_actions/applause`（鼓掌）。另一种方式是将机器人可靠吊装；使用 `actuators_cmds_override` 吊装测试时，底层状态只允许使用零位模式 `initial_pos` 或 PD 模式 `pd_brake`，禁止进入走路、挥手、鼓掌、跳舞等其他任何模式。

## 1. 无需写代码：覆盖头部关节

控制程序会在最终输出阶段读取 `communication/msg/ActuatorCmds` 类型的覆盖命令，并根据 `actuators_name` 只替换指定关节。其他关节仍由当前状态或策略控制，因此仅控制头部时不必创建 Mod，也不必发送完整的 31 维数组。

!!! warning "覆盖手臂或手部前先处理底层模型"
    `actuators_cmds_override` 只替换指定关节，不能让原有平衡模型自动适应新的手臂动作。机器人落地时，应先切换到不依赖手臂的 `hello` 或 `applause`，再开始发布手臂/手部覆盖命令。机器人吊装时不要进入这两个动作，只能停留在 `initial_pos` 或 `pd_brake`。

覆盖话题带有启动时的 `topic_prefix`：

| 环境 | 话题 |
| --- | --- |
| 仿真 | `/simulation/actuators_cmds_override` |
| 真机 | `/hardware/actuators_cmds_override` |

覆盖在零力矩状态下默认禁用。启动机器人并等待关节状态初始化后，先进入零位模式或正常控制状态。例如进入零位模式：

```bash
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 1}"

ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 0}"
```

!!! warning "按钮事件触发后必须复位为 0"
    `MotionCommands` 的按钮事件采用上升沿检测，程序会保存每个事件上一次收到的值。通过 ROS 手工发送任意非零按钮值后，必须再向同一按钮槽位发送 `0`，使其回到释放状态。否则下一次使用该按钮槽位时可能无法产生新的上升沿。

以下命令以 20 Hz 覆盖两个头部关节。`head_z_joint` 和 `head_y_joint` 的目标位置分别为 `0.20 rad` 和 `-0.10 rad`：

```bash
# 仿真
ros2 topic pub -r 20 \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds \
  '{
    actuators_name: ["head_z_joint", "head_y_joint"],
    pos: [0.20, -0.10],
    kp: [16.747, 16.747],
    kd: [1.066, 1.066]
  }'
```

真机使用相同消息，只需替换话题：

```bash
# 真机；执行前必须完成吊装并准备急停
ros2 topic pub -r 20 \
  /hardware/actuators_cmds_override \
  communication/msg/ActuatorCmds \
  '{
    actuators_name: ["head_z_joint", "head_y_joint"],
    pos: [0.20, -0.10],
    kp: [16.747, 16.747],
    kd: [1.066, 1.066]
  }'
```

`actuators_name` 决定命令中每个数组的关节顺序；`pos`、`kp` 和 `kd` 的长度必须与关节名数量相同。此处省略的 `vel` 和 `torque` 会按零处理。

默认覆盖超时为 `0.2 s`，因此不能使用 `--once` 长时间保持目标。停止上面的 20 Hz 发布命令后，覆盖会自动超时，并在 `0.2 s` 内混合回当前状态的输出。也可以主动发送空消息释放覆盖：

```bash
# 仿真；真机时将 simulation 替换为 hardware
ros2 topic pub --once \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds '{}'
```

需要发布随时间变化的头部轨迹时，让自己的 ROS 节点持续发布相同消息即可；每条新消息会原子替换上一条覆盖命令。若需要状态机集成、全身轨迹或更复杂的控制逻辑，再使用下面的 Mod 方式。

## 2. 31 关节顺序

`MotorFrame` 的 `qpos`、`kp` 和 `kd` 必须使用同一个关节布局。示例的公式数组采用以下顺序，角度单位为弧度：

| 下标 | 关节名 | 下标 | 关节名 |
| ---: | --- | ---: | --- |
| 0 | `waist_y_joint` | 16 | `l_shoulder_x_joint` |
| 1 | `waist_x_joint` | 17 | `l_shoulder_z_joint` |
| 2 | `waist_z_joint` | 18 | `l_elbow_y_joint` |
| 3 | `l_hip_y_joint` | 19 | `l_wrist_x_joint` |
| 4 | `l_hip_x_joint` | 20 | `l_wrist_y_joint` |
| 5 | `l_hip_z_joint` | 21 | `l_wrist_z_joint` |
| 6 | `l_knee_y_joint` | 22 | `r_shoulder_y_joint` |
| 7 | `l_ankle_y_joint` | 23 | `r_shoulder_x_joint` |
| 8 | `l_ankle_x_joint` | 24 | `r_shoulder_z_joint` |
| 9 | `r_hip_y_joint` | 25 | `r_elbow_y_joint` |
| 10 | `r_hip_x_joint` | 26 | `r_wrist_x_joint` |
| 11 | `r_hip_z_joint` | 27 | `r_wrist_y_joint` |
| 12 | `r_knee_y_joint` | 28 | `r_wrist_z_joint` |
| 13 | `r_ankle_y_joint` | 29 | `head_z_joint` |
| 14 | `r_ankle_x_joint` | 30 | `head_y_joint` |
| 15 | `l_shoulder_y_joint` |  |  |

示例会给 `MotorFrame` 显式绑定这个布局。运行时布局只要包含相同的 31 个具名关节，顺序可以不同；框架会按关节名把命令映射到实际顺序。

## 3. 创建 Mod

!!! danger "此 Mod 没有平衡能力"
    本例的 `on_update()` 只生成各关节的目标位置和增益，没有使用 IMU、足底接触或平衡策略，也不具备站立平衡、抗扰动或跌倒保护能力。它只能让关节按照写死的公式运动，不能让机器人自行站稳。

    为避免把“无平衡状态”和“吊装时只能保持零位或 PD”的规则混在一起，本教程只要求在仿真中运行该公式 Mod。真机只想验证关节动作时，使用上一节的 `actuators_cmds_override`：吊装机器人，并让底层状态始终保持 `initial_pos` 或 `pd_brake`。

```bash
cd ~/bxi_ws/bxi_rl_controller_ros2_example
mkdir -p src/bxi_example_py_elf3/mods/com.example.elf3_31dof
```

目录中只需要两个文件：

```text
src/bxi_example_py_elf3/mods/com.example.elf3_31dof/
├── mod.yaml
└── state.py
```

## 4. 编写 `state.py`

```python
import math

import numpy as np

from bxi_example_py_elf3.framework.mod_api import JointLayout, RobotControlState


ELF3_JOINT_NAMES = (
    "waist_y_joint", "waist_x_joint", "waist_z_joint",
    "l_hip_y_joint", "l_hip_x_joint", "l_hip_z_joint",
    "l_knee_y_joint", "l_ankle_y_joint", "l_ankle_x_joint",
    "r_hip_y_joint", "r_hip_x_joint", "r_hip_z_joint",
    "r_knee_y_joint", "r_ankle_y_joint", "r_ankle_x_joint",
    "l_shoulder_y_joint", "l_shoulder_x_joint", "l_shoulder_z_joint",
    "l_elbow_y_joint", "l_wrist_x_joint", "l_wrist_y_joint",
    "l_wrist_z_joint", "r_shoulder_y_joint", "r_shoulder_x_joint",
    "r_shoulder_z_joint", "r_elbow_y_joint", "r_wrist_x_joint",
    "r_wrist_y_joint", "r_wrist_z_joint", "head_z_joint",
    "head_y_joint",
)
ELF3_LAYOUT = JointLayout(ELF3_JOINT_NAMES, label="ELF3 31-DoF")


class Elf31DofState(RobotControlState):
    # 顺序与 ELF3_JOINT_NAMES 完全一致。前 29 项沿用零位模式增益，
    # 最后两项是头部关节增益。
    KP = np.array([
        500, 500, 300,
        300, 100, 100, 300, 50, 50,
        300, 100, 100, 300, 50, 50,
        100, 80, 80, 100, 20, 20, 20,
        100, 80, 80, 100, 20, 20, 20,
        16.747, 16.747,
    ], dtype=np.float32)
    KD = np.array([
        3, 3, 3,
        2.5, 2, 2, 2.5, 2, 2,
        2.5, 2, 2, 2.5, 2, 2,
        2.5, 2, 2, 2.5, 1, 1, 1,
        2.5, 2, 2, 2.5, 1, 1, 1,
        1.066, 1.066,
    ], dtype=np.float32)

    def __init__(self, name, state_id):
        super().__init__(name, state_id)
        self.elapsed = 0.0
        self.qpos = np.zeros(31, dtype=np.float32)

    def on_enter(self, ctx):
        if frozenset(ctx.robot_layout.names) != frozenset(ELF3_JOINT_NAMES):
            raise RuntimeError(
                "ELF3 关节集合不匹配: "
                f"expected={ELF3_JOINT_NAMES}, actual={ctx.robot_layout.names}"
            )
        self.elapsed = 0.0

    def on_update(self, ctx, dt):
        # 每周期从零位重新生成目标，避免把偏移逐帧累加。
        self.qpos.fill(0.0)
        phase = 2.0 * math.pi * 0.25 * self.elapsed

        # 写死的 31 自由度示例轨迹：腰腿保持零位，双臂和头部小幅摆动。
        self.qpos[15] = 0.15 * math.sin(phase)        # 左肩 y
        self.qpos[18] = 0.12 * math.sin(phase)        # 左肘 y
        self.qpos[22] = -0.15 * math.sin(phase)       # 右肩 y
        self.qpos[25] = -0.12 * math.sin(phase)       # 右肘 y
        self.qpos[29] = 0.10 * math.sin(phase)        # 头部 z
        self.qpos[30] = 0.06 * math.sin(2.0 * phase)  # 头部 y

        frame = self._motor_frame(
            ctx, self.qpos, self.KP, self.KD, layout=ELF3_LAYOUT
        )
        self._apply_frame(ctx, frame)
        self.elapsed += dt
```

关键点只有四个：

1. `qpos`、`KP`、`KD` 都是长度为 31 的 `float32` 数组，并按 `ELF3_LAYOUT` 解释，因此该状态每周期都给完整机器人布局发送命令。
2. `phase` 使用框架传入的 `dt` 累计，不依赖控制循环恰好运行了多少次。
3. `_motor_frame()` 复用状态内部的 `MotorFrame` 缓冲，`_apply_frame()` 将其交给框架。
4. 没有实现 `EntryFrameProvider` 或 `RunningFrameProvider`；所有轨迹只在 `on_update()` 中产生。

当前 `MotorFrame` 还支持 MIT 命令中的 `vel` 和 `torque`。本例调用 `_motor_frame()` 时没有提供这两个字段，框架会明确将它们填为零。

当前公式只让 6 个关节运动，但其余 25 个关节同样由 `qpos=0` 以及对应的 `kp/kd` 主动控制。需要改变动作时，直接修改 `on_update()` 中对应下标的公式；不要改变数组顺序。

## 5. 编写 `mod.yaml`

```yaml
schema: 1
id: com.example.elf3_31dof
name: ELF3 31 自由度公式轨迹
version: 1.0.0
api: ">=4,<5"
enable: true
entrypoint: null
visibility: public
requires:
  - id: com.bxi.basic_actions
    version: ">=1,<2"
conflicts: []
python_exports: []
runtime_requirements:
  python: []
  ros: []
  system: []

events:
  activate:
    slot: btn_10
    value: 99

states:
  formula_31dof:
    factory: state:Elf31DofState
    label: 31 自由度公式轨迹
    priority: 100
    group: Customer
    icon: waves
    confirm: true
    confirm_message: 此示例没有平衡能力，仅限仿真运行

routes:
  - from: com.bxi.basic_actions/initial_pos
    event: activate
    to: formula_31dof

  - from: formula_31dof
    event: com.bxi.basic_actions/initial_pos
    to: com.bxi.basic_actions/initial_pos
```

两条 route 都故意不写 `transition`。项目的 `elf3_state_machine.yaml` 将 `default_transition` 配置为 `instant`，所以状态会立即切换，并从下一个控制周期开始执行目标状态的 `on_update()`。这就是本例“不用过渡”的含义；如果项目修改了系统默认值，可在两条 route 上显式写 `transition: instant`。

示例只允许从 `com.bxi.basic_actions/initial_pos`（零位模式）进入。这不仅用于减小即时切换时的目标差异，也是因为该公式轨迹没有平衡能力；不要为它增加从 `normal`、走路或其他动作状态进入的 route。`btn_10=99` 用于进入本状态；按零位模式键可返回。这里不使用 `btn_10=10`，因为该组合已经由 `com.bxi.any_motion/activate` 占用。

## 6. 构建和运行

```bash
colcon build --packages-select bxi_example_py_elf3 \
  --symlink-install --merge-install
source install/setup.bash
```

先启动仿真：

```bash
ros2 launch bxi_example_py_elf3 example_demo.launch.py
```

启动后先发送零位模式命令：

```bash
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 1}"

ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_4: 0}"
```

机器人进入零位模式后，发送 `btn_10=99` 进入公式轨迹状态：

```bash
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_10: 99}"

# 必须释放 btn_10，否则后续 btn_10 动作可能无法触发
ros2 topic pub --once /motion_commands \
  communication/msg/MotionCommands "{btn_10: 0}"
```

发送 `btn_10=0` 只负责恢复按钮的释放状态，不会退出已经进入的公式轨迹状态。

加载成功时日志中应出现：

```text
[com.example.elf3_31dof]: loaded v1.0.0: .../com.example.elf3_31dof
```

状态完整名为 `com.example.elf3_31dof/formula_31dof`。

本教程中的公式轨迹 Mod 仅用于仿真演示，不应作为真机站立控制器。真机只需验证关节动作时，请改用 `actuators_cmds_override`；机器人吊装后底层状态只能保持 `initial_pos` 或 `pd_brake`。真机程序需要 root 权限，并应先停止后台自启动服务，避免两个控制程序同时向电机发送命令。启动方法见[运动控制开发指南](motioncontrol.md#启动机器人程序)。

## 常见问题

### 提示关节布局不匹配

先查看 `ctx.robot_layout.names` 的实际值。顺序不同不影响控制，框架会按照 `ELF3_LAYOUT` 中的关节名自动映射；只有缺少关节或出现不同关节名时才需要按照实际硬件版本更新布局和三个 31 维数组。

### 状态可以进入但机器人不动

确认已经执行最新工作空间的 `source install/setup.bash`，并检查启动日志是否加载了 `com.example.elf3_31dof`。如果使用非 `--symlink-install` 构建，修改 Mod 后需要重新构建。

### 切换瞬间有突跳

这是即时切换的预期风险。先将机器人切到零位模式，并让 `on_update()` 在 `elapsed=0` 时生成与零位一致的 `qpos`。若需要从任意姿态平滑进入，应改用 Transition；这不属于本最简示例。
