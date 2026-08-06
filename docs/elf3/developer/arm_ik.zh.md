# 使用 Pinocchio 最简求解 ELF3 手臂 IK

本文使用 Pinocchio 的阻尼最小二乘法，将手腕目标位姿转换为 ELF3 单臂 7 个关节角。页面同时提供左臂和右臂资源。示例只做离线逆运动学计算，不启动 ROS，也不会直接控制电机。

!!! danger "IK 结果不能未经验证直接发送到真机"
    本例只应用 URDF 关节限位，不检查自碰撞、环境碰撞、速度、加速度、力矩或奇异位形。必须先检查是否收敛，并在仿真中验证轨迹连续性和安全性。

## 1. 下载示例资源

下载以下左右臂脚本和 URDF，并放在同一个目录中：

- 左臂：[pinocchio_ik_solve.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve.py) 和 [elf3_arm_l.urdf](../../assets/elf3/developer/arm_ik/elf3_arm_l.urdf)
- 右臂：[pinocchio_ik_solve_r.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve_r.py) 和 [elf3_arm_r.urdf](../../assets/elf3/developer/arm_ik/elf3_arm_r.urdf)

目录结构应为：

```text
elf3_arm_ik/
├── elf3_arm_l.urdf
├── elf3_arm_r.urdf
├── pinocchio_ik_solve.py
└── pinocchio_ik_solve_r.py
```

两个 URDF 中都包含 STL 可视化和碰撞网格路径，但本例调用的是 `pin.buildModelFromUrdf()`，只构建运动学模型，不加载几何模型，因此运行最简 IK 不需要下载 STL 文件。

## 2. 安装 Pinocchio

建议在开发电脑的独立 Python 虚拟环境中运行，避免 Pinocchio 安装的 NumPy 版本影响 ROS 环境：

```bash
cd elf3_arm_ik
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pin scipy
```

!!! note "安装名与导入名不同"
    PyPI 包名是 `pin`，代码中的导入名是 `pinocchio`。不要把安装命令误写成 `pip install pinocchio`。

验证安装：

```bash
python -c "import pinocchio as pin; print(pin.__version__)"
```

本文已使用 `pin 4.1.0`、`numpy 2.2.6` 和 `scipy 1.15.3` 验证。其他兼容版本也可以使用。

## 3. 完整求解代码

### 左臂完整代码

下面的代码与可下载的 [pinocchio_ik_solve.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve.py) 完全一致：

```python
import numpy as np
import pinocchio as pin
from scipy.spatial.transform import Rotation as R


if __name__ == "__main__":
    # 从 URDF 创建机器人模型
    model = pin.buildModelFromUrdf("elf3_arm_l.urdf")
    data = model.createData()

    # 选择末端坐标系
    frame_id = model.getFrameId("l_wrist_z_link")

    # 设置目标位置和目标姿态
    target = pin.SE3(
        R.from_euler("xyz", [10, 0, 0], degrees=True).as_matrix(),
        np.array([0.1, 0, 0]),
    )

    # 初始关节角
    q = np.zeros(model.nq)

    max_iterations = 1000
    error_tolerance = 1e-5
    step_size = 0.1
    damping = 1e-6

    for i in range(max_iterations):
        # 正运动学，计算当前末端位姿
        pin.forwardKinematics(model, data, q)
        pin.updateFramePlacements(model, data)
        current = data.oMf[frame_id]

        # SE(3) 位姿误差：当前末端坐标系到目标坐标系的变换
        current_to_target = current.actInv(target)
        error = pin.log6(current_to_target).vector

        # 判断是否收敛
        if np.linalg.norm(error) < error_tolerance:
            break

        # 计算末端在局部坐标系下的雅可比矩阵
        jacobian = pin.computeFrameJacobian(
            model,
            data,
            q,
            frame_id,
            pin.ReferenceFrame.LOCAL,
        )

        # 将末端雅可比转换为 SE(3) 位姿误差的雅可比
        jacobian = -pin.Jlog6(current_to_target.inverse()) @ jacobian

        # 阻尼最小二乘法，计算关节角增量
        velocity = -jacobian.T @ np.linalg.solve(
            jacobian @ jacobian.T + damping * np.eye(6),
            error,
        )

        # 更新关节角，并限制在 URDF 给出的关节范围内
        q = pin.integrate(model, q, velocity * step_size)
        q = np.clip(q, model.lowerPositionLimit, model.upperPositionLimit)

    print(q)
```

### 用同一求解流程计算右臂

正文只保留一份完整代码。右臂的求解流程完全相同；可以直接下载 [pinocchio_ik_solve_r.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve_r.py)，或者复制上面的左臂代码并只替换两处：

- `elf3_arm_l.urdf` 改为 `elf3_arm_r.urdf`；
- `l_wrist_z_link` 改为 `r_wrist_z_link`。

两个脚本的求解流程相同：

1. 通过正运动学计算当前末端位姿。
2. 使用 `pin.log6()` 得到 6 维 SE(3) 位姿误差。
3. 计算末端局部坐标系中的雅可比矩阵。
4. 使用阻尼最小二乘公式计算关节速度：

   ```text
   v = -Jᵀ (J Jᵀ + λI)⁻¹ e
   ```

5. 使用 `pin.integrate()` 更新关节角，并裁剪到 URDF 限位。

### 末端坐标系的原点和朝向

左臂末端坐标系是 `l_wrist_z_link`，右臂是 `r_wrist_z_link`。根据随本文提供的简化 URDF：

- 末端原点位于腕部 X、Y、Z 三个转轴的交点，不是手掌中心或指尖。`wrist_y_joint` 和 `wrist_z_joint` 的 `<origin>` 都是 `xyz="0 0 0" rpy="0 0 0"`，因此这三个腕关节共用同一原点。
- 这里的 `base_link` 是简化单臂模型的根坐标系，原点就在该侧肩部第一个转轴中心，并不是完整机器人位于躯干或地面的 `base_link`。所以计算结果若要用于完整机器人模型，必须先做坐标变换。
- 当 7 个关节角全部为 0 时，末端原点相对这个 `base_link` 位于 `(0.256, 0, -0.256) m`：先从肩部沿 `-Z` 到肘部 `0.256 m`，再沿 `+X` 到腕部 `0.256 m`。左右臂的简化 URDF 在零位下相同。
- 所有关节的固定 `rpy` 都是 0，因此零位时末端坐标轴与 `base_link` 完全平行：末端 `+X/+Y/+Z` 分别指向 `base_link` 的 `+X/+Y/+Z`。按 ELF3 使用的 ROS 机身坐标约定，即 `+X` 向前、`+Y` 向机器人左侧、`+Z` 向上。关节转动后，末端轴会随腕部一起旋转。

`target.translation` 的单位是米，表示目标末端原点在上述简化 `base_link` 中的位置。`target.rotation` 表示目标末端坐标轴相对 `base_link` 的朝向。示例中的 `R.from_euler("xyz", [10, 0, 0], degrees=True)` 表示目标末端绕 X 轴旋转 10°，不是只给某一个腕关节增加 10°。

## 4. 运行并读取结果

必须在资源文件所在目录运行，因为脚本使用相对路径读取 URDF：

```bash
cd elf3_arm_ik
source .venv/bin/activate

# 左臂
python pinocchio_ik_solve.py

# 右臂
python pinocchio_ik_solve_r.py
```

左右臂脚本使用相同的目标位姿，当前都输出：

```text
[-0.18420714  0.14130363 -0.02609032 -0.95993     0.14621128  1.309
 -0.14385886]
```

左臂数组顺序由 `elf3_arm_l.urdf` 决定：

| 下标 | 关节名 | 结果（rad） |
| ---: | --- | ---: |
| 0 | `l_shoulder_y_joint` | -0.18420714 |
| 1 | `l_shoulder_x_joint` | 0.14130363 |
| 2 | `l_shoulder_z_joint` | -0.02609032 |
| 3 | `l_elbow_y_joint` | -0.95993 |
| 4 | `l_wrist_x_joint` | 0.14621128 |
| 5 | `l_wrist_y_joint` | 1.309 |
| 6 | `l_wrist_z_joint` | -0.14385886 |

右臂输出使用相同的 7 个数值，但按 `elf3_arm_r.urdf` 对应到：

```text
r_shoulder_y_joint, r_shoulder_x_joint, r_shoulder_z_joint,
r_elbow_y_joint, r_wrist_x_joint, r_wrist_y_joint, r_wrist_z_joint
```

!!! warning "当前目标没有达到配置的收敛容差"
    使用原始参数运行 1000 次后，误差范数约为 `0.1787`，高于 `1e-5`。肘关节到达下限 `-0.95993 rad`，腕部 Y 关节到达上限 `1.309 rad`。脚本仍会打印最后一次迭代结果，因此“得到数组”不代表“成功到达目标”。

实际项目应在循环结束后重新计算误差，并且只有误差小于容差时才接受结果。若未收敛，可调整目标位姿、初始关节角、步长或阻尼。

## 5. 修改目标位姿

修改目标位置：

```python
target_position = np.array([x, y, z])  # 单位：m，base_link 坐标系
```

修改目标姿态：

```python
target_rotation = R.from_euler(
    "xyz",
    [roll, pitch, yaw],
    degrees=True,
).as_matrix()
```

组合为 Pinocchio 位姿：

```python
target = pin.SE3(target_rotation, target_position)
```

7 自由度手臂对 6 维末端位姿存在冗余，同一目标可能有多组解。初始值 `q`、阻尼和步长会影响最终结果；连续轨迹通常应以上一帧解作为下一帧初值，避免关节角跳变。

## 6. 将结果用于关节覆盖

IK 结果只是关节目标。需要在仿真中验证时，可以使用
[`actuators_cmds_override`](mod_api_31dof_control.md#1-无需写代码覆盖头部关节) 按关节名覆盖左臂。发布频率必须高于覆盖超时要求；当前默认超时为 `0.2 s`。

```bash
ros2 topic pub -r 20 \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds \
  '{
    actuators_name: [
      "l_shoulder_y_joint", "l_shoulder_x_joint",
      "l_shoulder_z_joint", "l_elbow_y_joint",
      "l_wrist_x_joint", "l_wrist_y_joint", "l_wrist_z_joint"
    ],
    pos: [
      -0.18420714, 0.14130363, -0.02609032, -0.95993,
      0.14621128, 1.309, -0.14385886
    ],
    kp: [54.224, 54.224, 16.747, 54.224, 16.747, 16.747, 16.747],
    kd: [3.452, 3.452, 1.066, 3.452, 1.066, 1.066, 1.066]
  }'
```

按 `Ctrl+C` 停止持续发布后，覆盖会超时并混合回当前状态。也可以主动释放：

```bash
ros2 topic pub --once \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds '{}'
```

真机使用 `/hardware/actuators_cmds_override`。控制右臂时，将命令中的 7 个 `l_` 关节名替换为对应的 `r_` 关节名。由于当前示例解包含两个限位值，不应直接用于真机。
