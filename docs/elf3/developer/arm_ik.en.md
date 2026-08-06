# Minimal ELF3 Arm IK with Pinocchio

This guide uses Pinocchio's damped least-squares method to convert a wrist target pose into seven ELF3 single-arm joint angles. Resources for both the left and right arms are provided. It performs offline inverse kinematics only; it does not start ROS or command any motors.

!!! danger "Never send an unverified IK result directly to hardware"
    This example applies only the URDF joint limits. It does not check self-collision, environment collision, velocity, acceleration, torque, or singular configurations. Verify convergence and validate trajectory continuity and safety in simulation first.

## 1. Download the example resources

Download the scripts and URDFs for both arms into the same directory:

- Left arm: [pinocchio_ik_solve.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve.py) and [elf3_arm_l.urdf](../../assets/elf3/developer/arm_ik/elf3_arm_l.urdf)
- Right arm: [pinocchio_ik_solve_r.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve_r.py) and [elf3_arm_r.urdf](../../assets/elf3/developer/arm_ik/elf3_arm_r.urdf)

The directory should look like this:

```text
elf3_arm_ik/
├── elf3_arm_l.urdf
├── elf3_arm_r.urdf
├── pinocchio_ik_solve.py
└── pinocchio_ik_solve_r.py
```

Both URDFs contain STL paths for visual and collision geometry. This example calls `pin.buildModelFromUrdf()` to build only the kinematic model, so the STL files are not required for the minimal IK solver.

## 2. Install Pinocchio

Use an isolated Python environment on the development computer so Pinocchio's NumPy dependencies do not affect the ROS environment:

```bash
cd elf3_arm_ik
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install pin scipy
```

!!! note "The package and import names differ"
    The PyPI package is named `pin`, while Python code imports it as `pinocchio`. Do not replace the command with `pip install pinocchio`.

Verify the installation:

```bash
python -c "import pinocchio as pin; print(pin.__version__)"
```

This guide was verified with `pin 4.1.0`, `numpy 2.2.6`, and `scipy 1.15.3`. Other compatible versions may also work.

## 3. Complete solver code

### Complete left-arm code

The code below exactly matches the downloadable [pinocchio_ik_solve.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve.py):

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

### Use the same solver for the right arm

This page keeps only one complete code listing because the solver flow is identical for both arms. For the right arm, download [pinocchio_ik_solve_r.py](../../assets/elf3/developer/arm_ik/pinocchio_ik_solve_r.py), or copy the left-arm code above and change only these two strings:

- Change `elf3_arm_l.urdf` to `elf3_arm_r.urdf`.
- Change `l_wrist_z_link` to `r_wrist_z_link`.

Both scripts use the same solver sequence:

1. Compute the current end-frame pose with forward kinematics.
2. Obtain the six-dimensional SE(3) pose error with `pin.log6()`.
3. Compute the frame Jacobian in the local frame.
4. Compute joint velocity with damped least squares:

   ```text
   v = -Jᵀ (J Jᵀ + λI)⁻¹ e
   ```

5. Update the configuration with `pin.integrate()` and clip it to the URDF limits.

### End-frame origin and orientation

The left-arm end frame is `l_wrist_z_link`; the right-arm frame is `r_wrist_z_link`. In the simplified URDFs supplied with this guide:

- The end-frame origin is at the common intersection of the wrist X, Y, and Z rotation axes, not at the palm centre or a fingertip. Both `wrist_y_joint` and `wrist_z_joint` have `<origin xyz="0 0 0" rpy="0 0 0">`, so the three wrist joints share one origin.
- `base_link` is the root of the simplified single-arm model. Its origin is at the first shoulder-axis centre for that arm; it is not a full-robot base frame located at the torso or on the ground. Transform the pose before using it with a full-robot model.
- With all seven joint angles at zero, the end-frame origin is `(0.256, 0, -0.256) m` in this `base_link`: the chain first goes `0.256 m` along `-Z` from shoulder to elbow and then `0.256 m` along `+X` from elbow to wrist. The simplified left- and right-arm URDFs use the same zero-position geometry.
- Every fixed joint `rpy` is zero. At the zero configuration, the end-frame `+X/+Y/+Z` axes therefore align exactly with the corresponding `base_link` axes. Under ELF3's ROS body-frame convention, `+X` points forward, `+Y` to the robot's left, and `+Z` upward. The end axes rotate with the wrist as the joints move.

`target.translation`, in metres, is the desired end-frame origin expressed in the simplified `base_link`. `target.rotation` is the desired orientation of the end-frame axes relative to `base_link`. In the example, `R.from_euler("xyz", [10, 0, 0], degrees=True)` requests an end frame rotated 10 degrees about X; it does not simply add 10 degrees to one wrist joint.

## 4. Run and interpret the result

Run from the directory containing the resources because both scripts open their URDF through a relative path:

```bash
cd elf3_arm_ik
source .venv/bin/activate

# Left arm
python pinocchio_ik_solve.py

# Right arm
python pinocchio_ik_solve_r.py
```

Both scripts use the same target pose and currently print:

```text
[-0.18420714  0.14130363 -0.02609032 -0.95993     0.14621128  1.309
 -0.14385886]
```

`elf3_arm_l.urdf` defines the left-arm array order:

| Index | Joint | Result (rad) |
| ---: | --- | ---: |
| 0 | `l_shoulder_y_joint` | -0.18420714 |
| 1 | `l_shoulder_x_joint` | 0.14130363 |
| 2 | `l_shoulder_z_joint` | -0.02609032 |
| 3 | `l_elbow_y_joint` | -0.95993 |
| 4 | `l_wrist_x_joint` | 0.14621128 |
| 5 | `l_wrist_y_joint` | 1.309 |
| 6 | `l_wrist_z_joint` | -0.14385886 |

The right-arm output uses the same seven numeric values, mapped by `elf3_arm_r.urdf` to:

```text
r_shoulder_y_joint, r_shoulder_x_joint, r_shoulder_z_joint,
r_elbow_y_joint, r_wrist_x_joint, r_wrist_y_joint, r_wrist_z_joint
```

!!! warning "The current target does not meet the configured tolerance"
    After 1000 iterations with the original parameters, the error norm is approximately `0.1787`, above `1e-5`. The elbow reaches its lower limit of `-0.95993 rad`, and wrist Y reaches its upper limit of `1.309 rad`. The script still prints the final iterate, so receiving an array does not mean the target was reached successfully.

Production code should recompute the error after the loop and accept the result only when it is below the tolerance. If convergence fails, adjust the target pose, initial configuration, step size, or damping.

## 5. Change the target pose

Change the target position with:

```python
target_position = np.array([x, y, z])  # metres, in base_link
```

Change the target orientation with:

```python
target_rotation = R.from_euler(
    "xyz",
    [roll, pitch, yaw],
    degrees=True,
).as_matrix()
```

Combine them into a Pinocchio pose:

```python
target = pin.SE3(target_rotation, target_position)
```

A seven-DoF arm is redundant for a six-dimensional end pose, so the same target may have multiple solutions. The initial `q`, damping, and step size affect the result. For continuous trajectories, use the previous solution as the next initial configuration to avoid joint jumps.

## 6. Use the result as a joint override

The IK result is only a joint target. To validate it in simulation, use
[`actuators_cmds_override`](mod_api_31dof_control.md#1-no-code-head-joint-override) to override the named left-arm joints. The publishing rate must satisfy the override timeout; the current default is `0.2 s`.

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

Press `Ctrl+C` to stop continuous publication; the override then times out and blends back to the current state. It can also be released explicitly:

```bash
ros2 topic pub --once \
  /simulation/actuators_cmds_override \
  communication/msg/ActuatorCmds '{}'
```

Use `/hardware/actuators_cmds_override` on hardware. To control the right arm, replace the seven `l_` joint names in the command with their corresponding `r_` names. Because the current example solution contains two limit values, do not send it directly to hardware.
