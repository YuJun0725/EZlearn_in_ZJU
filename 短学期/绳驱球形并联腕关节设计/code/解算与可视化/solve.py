import numpy as np
from itertools import product

sqrt3 = np.sqrt(3)


def rot_x(a):
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [1, 0, 0],
        [0, c, -s],
        [0, s,  c]
    ], dtype=float)


def rot_y(a):
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [ c, 0, s],
        [ 0, 1, 0],
        [-s, 0, c]
    ], dtype=float)


def rot_z(a):
    c = np.cos(a)
    s = np.sin(a)
    return np.array([
        [c, -s, 0],
        [s,  c, 0],
        [0,  0, 1]
    ], dtype=float)


def rpy_to_R(yaw, pitch, roll, degrees=True):
    """
    ZYX顺序:
        R = Rz(yaw) @ Ry(pitch) @ Rx(roll)

    yaw   : 绕 Z 轴
    pitch : 绕 Y 轴
    roll  : 绕 X 轴
    """
    if degrees:
        yaw, pitch, roll = np.deg2rad([yaw, pitch, roll])

    return rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)


def wrap_to_pi(angle):
    """
    把弧度角限制到 [-pi, pi)
    """
    return (angle + np.pi) % (2 * np.pi) - np.pi


def wrap_to_180(angle):
    """
    把角度制限制到 [-180, 180)
    """
    return (angle + 180.0) % 360.0 - 180.0


def unwrap_to_reference(theta, reference, degrees=True):
    """
    将 theta 展开到 reference 附近，避免 359° 和 -1° 这种跳变。
    """
    theta = np.asarray(theta, dtype=float)
    reference = np.asarray(reference, dtype=float)

    if degrees:
        return reference + wrap_to_180(theta - reference)
    else:
        return reference + wrap_to_pi(theta - reference)


def normalize(v):
    v = np.asarray(v, dtype=float).reshape(3)
    n = np.linalg.norm(v)
    if n < 1e-12:
        raise ValueError("向量长度接近0，无法归一化")
    return v / n


def solve_theta_candidates_single(
    w0,
    v0,
    yaw,
    pitch,
    roll,
    alpha=None,
    degrees=True,
    check_initial=True
):
    """
    求单条支链的两个候选解，并给每个解标记 mode。

    模型:
        w_i = Rz(theta_i) * w_i0
        v_i = R * v_i0
        w_i^T v_i = cos(alpha_i)

    最终形式:
        A cos(theta) + B sin(theta) = C

    两个解:
        theta_plus  = phi + delta   -> mode = +1
        theta_minus = phi - delta   -> mode = -1
    """

    w0 = normalize(w0)
    v0 = normalize(v0)

    if degrees and alpha is not None:
        alpha = np.deg2rad(alpha)

    # 如果没有给 alpha，则用初始状态自动计算 alpha
    # 这样可以保证 RPY=0 时 theta=0 是其中一个解
    if alpha is None:
        cos_alpha = np.dot(w0, v0)
    else:
        cos_alpha = np.cos(alpha)

        if check_initial:
            init_dot = np.dot(w0, v0)
            if abs(init_dot - cos_alpha) > 1e-6:
                raise ValueError(
                    "alpha 与初始 w0、v0 不一致。\n"
                    "如果希望 RPY=0 时 theta=0，必须满足 w0^T v0 = cos(alpha)。\n"
                    f"当前 w0^T v0 = {init_dot:.8f}, cos(alpha) = {cos_alpha:.8f}"
                )

    cos_alpha = np.clip(cos_alpha, -1.0, 1.0)

    # 当前平台姿态矩阵
    R = rpy_to_R(yaw, pitch, roll, degrees=degrees)

    # 当前平台侧向量 v_i
    v = R @ v0

    wx, wy, wz = w0
    vx, vy, vz = v

    # 展开:
    # (Rz(theta) w0)^T v = cos(alpha)
    #
    # 得:
    # A cos(theta) + B sin(theta) = C
    A = wx * vx + wy * vy
    B = wx * vy - wy * vx
    C = cos_alpha - wz * vz

    rho = np.hypot(A, B)

    if rho < 1e-12:
        raise ValueError("rho 太小，该姿态下 theta 无法稳定求解")

    q = C / rho

    if abs(q) > 1.0 + 1e-10:
        raise ValueError(
            f"无解，|C/rho| = {abs(q):.8f} > 1，可能超出工作空间"
        )

    q = np.clip(q, -1.0, 1.0)

    phi = np.arctan2(B, A)
    delta = np.arccos(q)

    theta_plus = phi + delta
    theta_minus = phi - delta

    # 归一化到 [-pi, pi)
    theta_plus = wrap_to_pi(theta_plus)
    theta_minus = wrap_to_pi(theta_minus)

    if degrees:
        theta_plus = np.rad2deg(theta_plus)
        theta_minus = np.rad2deg(theta_minus)

    candidates = [
        {
            "theta": theta_plus,
            "mode": +1
        },
        {
            "theta": theta_minus,
            "mode": -1
        }
    ]

    return candidates


def inverse_kinematics_all_solutions_with_modes(
    w0_list,
    v0_list,
    yaw,
    pitch,
    roll,
    alpha_list=None,
    degrees=True
):
    """
    返回所有组合解以及对应 working mode。

    如果有3条支链，每条支链2个解，则最多返回 2^3 = 8 组解。

    每组解的数据结构:
        {
            "theta": np.array([theta1, theta2, theta3]),
            "working_mode": (+1, -1, +1)
        }
    """

    w0_list = np.asarray(w0_list, dtype=float)
    v0_list = np.asarray(v0_list, dtype=float)

    n = w0_list.shape[0]

    if v0_list.shape[0] != n:
        raise ValueError("w0_list 和 v0_list 数量不一致")

    if alpha_list is None:
        alpha_list = [None] * n
    else:
        alpha_list = np.asarray(alpha_list, dtype=float)
        if len(alpha_list) != n:
            raise ValueError("alpha_list 长度必须和支链数量一致")

    candidates_all = []

    for i in range(n):
        candidates = solve_theta_candidates_single(
            w0=w0_list[i],
            v0=v0_list[i],
            yaw=yaw,
            pitch=pitch,
            roll=roll,
            alpha=alpha_list[i],
            degrees=degrees
        )
        candidates_all.append(candidates)

    all_solutions = []

    for combo in product(*candidates_all):
        theta = np.array([item["theta"] for item in combo], dtype=float)
        working_mode = tuple(item["mode"] for item in combo)

        all_solutions.append({
            "theta": theta,
            "working_mode": working_mode
        })

    return all_solutions


def choose_solution_closest_to_reference(
    all_solutions,
    reference_theta,
    degrees=True
):
    """
    从所有解中选出最接近 reference_theta 的那一组。
    通常用于初始姿态下自动识别 working mode。
    """

    reference_theta = np.asarray(reference_theta, dtype=float)

    best_solution = None
    best_cost = np.inf

    for sol in all_solutions:
        theta = unwrap_to_reference(
            sol["theta"],
            reference_theta,
            degrees=degrees
        )

        cost = np.linalg.norm(theta - reference_theta)

        if cost < best_cost:
            best_cost = cost
            best_solution = {
                "theta": theta,
                "working_mode": sol["working_mode"],
                "cost": cost
            }

    return best_solution


def choose_solution_by_working_mode(
    all_solutions,
    working_mode,
    reference_theta=None,
    degrees=True
):
    """
    根据指定 working mode 选解。

    如果 reference_theta 不为空，则把角度展开到 reference_theta 附近，
    用于避免 359° 和 -1° 这种显示跳变。
    """

    candidates = [
        sol for sol in all_solutions
        if sol["working_mode"] == tuple(working_mode)
    ]

    if len(candidates) == 0:
        raise ValueError(f"没有找到 working_mode = {working_mode} 对应的解")

    sol = candidates[0]

    theta = sol["theta"]

    if reference_theta is not None:
        theta = unwrap_to_reference(
            theta,
            reference_theta,
            degrees=degrees
        )

    return {
        "theta": theta,
        "working_mode": sol["working_mode"]
    }


def print_all_solutions(all_solutions, title="所有解"):
    print(f"\n{title}：")
    for i, sol in enumerate(all_solutions, 1):
        theta = sol["theta"]
        mode = sol["working_mode"]
        print(
            f"解 {i}: "
            f"theta = [{theta[0]: .6f}, {theta[1]: .6f}, {theta[2]: .6f}], "
            f"working_mode = {mode}"
        )


if __name__ == "__main__":

    # =========================
    # 1. 初始机构参数
    # =========================

    # w_i0：初始主动臂方向
    w0_list = np.array([
        [1, 0, -1],
        [-0.5, sqrt3 / 2, -1],
        [-0.5, -sqrt3 / 2, -1]
    ], dtype=float)

    # v_i0：初始平台侧方向
    v0_list = np.array([
        [0.00, -1, 0.0],
        [sqrt3 / 2, 0.5, 0.0],
        [-sqrt3 / 2, 0.5, 0.0],
        
    ], dtype=float)

    # =========================
    # 2. 初始姿态
    # =========================

    init_yaw = 0.0
    init_pitch = 0.0
    init_roll = 0.0

    # 初始电机角，按你的定义应该是 [0, 0, 0]
    theta_home = np.array([0.0, 0.0, 0.0])

    # 初始姿态下所有解
    init_solutions = inverse_kinematics_all_solutions_with_modes(
        w0_list=w0_list,
        v0_list=v0_list,
        yaw=init_yaw,
        pitch=init_pitch,
        roll=init_roll,
        alpha_list=None,
        degrees=True
    )

    # 保留初始姿态计算，不打印调试信息。

    # 自动选择初始 working mode：
    # 选初始姿态下最接近 theta_home = [0,0,0] 的那组解
    # init_selected = choose_solution_closest_to_reference(
    #     all_solutions=init_solutions,
    #     reference_theta=theta_home,
    #     degrees=True
    # )

    # initial_working_mode = init_selected["working_mode"]

    # print("\n初始选中的解：")
    # print(f"theta_home_solution = {init_selected['theta']}")
    # print(f"initial_working_mode = {initial_working_mode}")

    initial_working_mode = (1, 1, 1)

    # =========================
    # 3. 目标姿态
    # =========================

    # 从终端输入目标 RPY，单位为度，顺序为 yaw、pitch、roll
    try:
        target_yaw = float(input("请输入目标 yaw (deg): ").strip())
        target_pitch = float(input("请输入目标 pitch (deg): ").strip())
        target_roll = float(input("请输入目标 roll (deg): ").strip())
    except ValueError:
        raise SystemExit("欧拉角必须输入数字，例如：20、-10、30")

    target_solutions = inverse_kinematics_all_solutions_with_modes(
        w0_list=w0_list,
        v0_list=v0_list,
        yaw=target_yaw,
        pitch=target_pitch,
        roll=target_roll,
        alpha_list=None,
        degrees=True
    )

    print_all_solutions(
        target_solutions,
        title=f"目标姿态 RPY = {target_yaw},{target_pitch},{target_roll} 下的所有解"
    )

    # =========================
    # 4. 根据初始 working mode 选择最终解
    # =========================

    final_solution = choose_solution_by_working_mode(
        all_solutions=target_solutions,
        working_mode=initial_working_mode,
        reference_theta=theta_home,
        degrees=True
    )

    print("\n最终选解结果：")
    print(f"theta_final = {final_solution['theta']}")
