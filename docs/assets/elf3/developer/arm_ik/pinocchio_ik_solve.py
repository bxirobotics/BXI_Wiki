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
