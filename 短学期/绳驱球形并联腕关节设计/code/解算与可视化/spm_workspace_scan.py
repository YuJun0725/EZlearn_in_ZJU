import numpy as np
import pandas as pd
from scipy.optimize import least_squares
from scipy.spatial import ConvexHull


# ============================================================
# 1. 扫描参数
# ============================================================

# theta 是从初始位置开始的增量角
THETA_MIN_DEG = np.array([-70.0, -70.0, -70.0])
THETA_MAX_DEG = np.array([70.0, 70.0, 70.0])
STEP_DEG = 2.0

THETA_HOME_DEG = np.array([0.0, 0.0, 0.0])

ZETA_MIN = 0.3
FK_ERROR_MAX = 1e-8
POSE_JUMP_MAX_DEG = 30.0

# 支链圆周方向最小间隔。太小会认为支链接近交叉/干涉。
MIN_BRANCH_SEPARATION_DEG = 5.0

OUTPUT_CSV = "workspace_simulation.csv"
OUTPUT_POLYTOPE = "workspace_joint_polytope.npz"


# ============================================================
# 2. 机构参数
# ============================================================

sqrt2 = np.sqrt(2.0)
sqrt3 = np.sqrt(3.0)
sqrt6 = np.sqrt(6.0)

# 三个输入转动副同轴，方向为 z 轴正方向
u0 = np.array([0.0, 0.0, 1.0])

# 底部输入侧初始轴线 w_i0
w0_list = np.array([
    [sqrt2 / 2.0, 0.0, -sqrt2 / 2.0],
    [-sqrt2 / 4.0, sqrt6 / 4.0, -sqrt2 / 2.0],
    [-sqrt2 / 4.0, -sqrt6 / 4.0, -sqrt2 / 2.0],
])

# 动平台侧初始轴线 v_i0，在动平台坐标系下固定
v0_list = np.array([
    [0.0, -1.0, 0.0],
    [sqrt3 / 2.0, 1.0 / 2.0, 0.0],
    [-sqrt3 / 2.0, 1.0 / 2.0, 0.0],
])

# 当前给定几何中 w_i0 dot v_i0 = 0，所以 alpha_i = 90 deg。
# 如果你的实际夹角不是 90 deg，把这里改成 np.cos(np.deg2rad([...]))。
COS_ALPHA = np.array([0.0, 0.0, 0.0])


# ============================================================
# 3. 基础函数
# ============================================================

def normalize(a):
    a = np.asarray(a, dtype=float)
    n = np.linalg.norm(a)

    if n < 1e-12:
        raise ValueError("zero vector cannot be normalized")

    return a / n


def rot_x(angle_rad):
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)

    return np.array([
        [1.0, 0.0, 0.0],
        [0.0, c, -s],
        [0.0, s, c],
    ])


def rot_y(angle_rad):
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)

    return np.array([
        [c, 0.0, s],
        [0.0, 1.0, 0.0],
        [-s, 0.0, c],
    ])


def rot_z(angle_rad):
    c = np.cos(angle_rad)
    s = np.sin(angle_rad)

    return np.array([
        [c, -s, 0.0],
        [s, c, 0.0],
        [0.0, 0.0, 1.0],
    ])


def euler_zyx_to_R(euler_rad):
    """
    euler_rad = [yaw, pitch, roll]
    R = Rz(yaw) Ry(pitch) Rx(roll)
    """
    yaw, pitch, roll = euler_rad
    return rot_z(yaw) @ rot_y(pitch) @ rot_x(roll)


def rotation_distance(R1, R2):
    R_rel = R1.T @ R2
    value = (np.trace(R_rel) - 1.0) / 2.0
    value = np.clip(value, -1.0, 1.0)
    return np.arccos(value)

def platform_normal_and_tilt(R_platform):
    """
    计算动平台法向量及其与基座 z 轴的夹角。

    假设动平台法向量是平台坐标系下的 +z 轴:
        n0 = [0, 0, 1]

    在基坐标系下:
        n = R_platform @ n0

    tilt 是 n 和基座 z 轴 [0,0,1] 的夹角。
    """
    n0 = np.array([0.0, 0.0, 1.0])
    z0 = np.array([0.0, 0.0, 1.0])

    normal = R_platform @ n0
    normal = normalize(normal)

    cos_tilt = np.dot(normal, z0)
    cos_tilt = np.clip(cos_tilt, -1.0, 1.0)

    tilt_rad = np.arccos(cos_tilt)
    tilt_deg = np.rad2deg(tilt_rad)

    return normal, tilt_deg



def azimuth_angle(vec):
    """
    向量在 xy 平面投影的方位角，范围 [0, 2*pi)。
    """
    angle = np.arctan2(vec[1], vec[0])
    return angle % (2.0 * np.pi)


def is_cyclic_same_order(current_order, reference_order):
    """
    判断圆周排列顺序是否相同，允许整体循环平移。
    例如 [0,1,2]、[1,2,0]、[2,0,1] 视为同一圆周顺序。
    """
    current_order = list(current_order)
    reference_order = list(reference_order)
    n = len(reference_order)

    for shift in range(n):
        if current_order == reference_order[shift:] + reference_order[:shift]:
            return True

    return False


def circular_gaps(angles):
    """
    计算圆周上相邻方位角间隔。
    """
    angles = np.sort(np.asarray(angles))
    gaps = []

    for i in range(len(angles) - 1):
        gaps.append(angles[i + 1] - angles[i])

    gaps.append(angles[0] + 2.0 * np.pi - angles[-1])

    return np.array(gaps)


# ============================================================
# 4. 当前 w_i 和 v_i
# ============================================================

def compute_w_list(theta_rad):
    """
    theta_i 是从初始位置开始的增量角。

    w_i(theta_i) = Rz(theta_i) w_i0
    """
    w_list = []

    for i in range(3):
        w_i = rot_z(theta_rad[i]) @ normalize(w0_list[i])
        w_list.append(normalize(w_i))

    return np.array(w_list)


def compute_v_list(R_platform):
    """
    v_i = R v_i0
    """
    v_list = []

    for i in range(3):
        v_i = R_platform @ normalize(v0_list[i])
        v_list.append(normalize(v_i))

    return np.array(v_list)


# 初始支链圆周顺序
INITIAL_BRANCH_AZIMUTHS = np.array([
    azimuth_angle(w0_list[0]),
    azimuth_angle(w0_list[1]),
    azimuth_angle(w0_list[2]),
])

INITIAL_BRANCH_ORDER = list(np.argsort(INITIAL_BRANCH_AZIMUTHS))
MIN_BRANCH_SEPARATION_RAD = np.deg2rad(MIN_BRANCH_SEPARATION_DEG)


def check_branch_order(theta_rad):
    """
    检查三条支链绕公共 z 轴的圆周排列顺序是否保持不变。

    如果顺序改变，说明同轴圆周方向发生交叉，判为不可行。
    """
    w_list = compute_w_list(theta_rad)

    current_azimuths = np.array([
        azimuth_angle(w_list[0]),
        azimuth_angle(w_list[1]),
        azimuth_angle(w_list[2]),
    ])

    current_order = list(np.argsort(current_azimuths))

    same_order = is_cyclic_same_order(
        current_order,
        INITIAL_BRANCH_ORDER,
    )

    if not same_order:
        return False, "branch_order_changed"

    gaps = circular_gaps(current_azimuths)

    if np.min(gaps) < MIN_BRANCH_SEPARATION_RAD:
        return False, "branch_too_close"

    return True, "branch_order_ok"


# ============================================================
# 5. 正运动学
# ============================================================

def fk_residual(euler_rad, theta_rad):
    """
    正运动学方程:

        f_i = (Rz(theta_i) w_i0)^T (R v_i0) - cos(alpha_i)

    目标:
        f_i = 0
    """
    R_platform = euler_zyx_to_R(euler_rad)

    w_list = compute_w_list(theta_rad)
    v_list = compute_v_list(R_platform)

    residual = np.zeros(3)

    for i in range(3):
        residual[i] = np.dot(w_list[i], v_list[i]) - COS_ALPHA[i]

    return residual


def forward_kinematics(theta_rad, initial_euler_rad):
    """
    已知 theta，求平台姿态 R。

    返回:
        R_platform
        euler_rad = [yaw, pitch, roll]
        error
        ok
    """
    result = least_squares(
        fk_residual,
        initial_euler_rad,
        args=(theta_rad,),
        xtol=1e-12,
        ftol=1e-12,
        gtol=1e-12,
        max_nfev=300,
    )

    euler_rad = result.x
    R_platform = euler_zyx_to_R(euler_rad)
    error = np.linalg.norm(fk_residual(euler_rad, theta_rad))

    ok = error <= FK_ERROR_MAX

    return R_platform, euler_rad, error, ok


# ============================================================
# 6. 雅各比矩阵
# ============================================================

def compute_jacobian(theta_rad, R_platform):
    """
    按你给出的式子:

        (v_i x w_i)^T omega
        =
        [u0^T (v_i x w_i)] theta_dot_i

    构造:

        n_i = v_i x w_i
        A[i, :] = n_i
        B[i, i] = u0^T n_i
        J = A^{-1} B
    """
    w_list = compute_w_list(theta_rad)
    v_list = compute_v_list(R_platform)

    A = np.zeros((3, 3))
    B = np.zeros((3, 3))

    for i in range(3):
        n_i = np.cross(v_list[i], w_list[i])

        A[i, :] = n_i
        B[i, i] = np.dot(u0, n_i)

    try:
        J = np.linalg.solve(A, B)
    except np.linalg.LinAlgError:
        return None, A, B

    return J, A, B


def conditioning_index(J):
    """
    zeta = sigma_min / sigma_max
    zeta 越接近 0，越接近奇异。
    """
    if J is None:
        return 0.0

    try:
        s = np.linalg.svd(J, compute_uv=False)
    except np.linalg.LinAlgError:
        return 0.0

    sigma_max = np.max(s)
    sigma_min = np.min(s)

    if sigma_max < 1e-12:
        return 0.0

    return sigma_min / sigma_max


# ============================================================
# 7. 采样点生成
# ============================================================

def generate_grid_points():
    theta1_vals = np.arange(
        THETA_MIN_DEG[0],
        THETA_MAX_DEG[0] + STEP_DEG,
        STEP_DEG,
    )
    theta2_vals = np.arange(
        THETA_MIN_DEG[1],
        THETA_MAX_DEG[1] + STEP_DEG,
        STEP_DEG,
    )
    theta3_vals = np.arange(
        THETA_MIN_DEG[2],
        THETA_MAX_DEG[2] + STEP_DEG,
        STEP_DEG,
    )

    points = []

    # snake 顺序，让相邻点尽量接近，便于正运动学连续跟踪
    for i, t1 in enumerate(theta1_vals):
        theta2_iter = theta2_vals if i % 2 == 0 else theta2_vals[::-1]

        for j, t2 in enumerate(theta2_iter):
            theta3_iter = theta3_vals if j % 2 == 0 else theta3_vals[::-1]

            for t3 in theta3_iter:
                points.append(np.array([t1, t2, t3], dtype=float))

    return points


# ============================================================
# 8. 工作空间扫描
# ============================================================

def scan_workspace():
    points = generate_grid_points()
    results = []

    theta_home_rad = np.deg2rad(THETA_HOME_DEG)

    # 假设初始位置平台姿态接近 yaw=pitch=roll=0。
    initial_euler_rad = np.deg2rad(np.array([0.0, 0.0, 0.0]))

    R_home, home_euler_rad, home_error, home_ok = forward_kinematics(
        theta_home_rad,
        initial_euler_rad,
    )

    if not home_ok:
        raise RuntimeError(f"Home FK failed. error={home_error}")

    previous_euler_rad = home_euler_rad
    previous_R = R_home

    print("Initial branch order:", INITIAL_BRANCH_ORDER)
    print("Initial branch azimuths deg:", np.rad2deg(INITIAL_BRANCH_AZIMUTHS))
    print("Home euler [yaw, pitch, roll] deg:", np.rad2deg(home_euler_rad))
    print("Home FK error:", home_error)
    print("Total points:", len(points))

    for k, theta_deg in enumerate(points):
        theta_rad = np.deg2rad(theta_deg)

        order_ok, order_message = check_branch_order(theta_rad)

        if not order_ok:
            results.append({
                "theta1_deg": theta_deg[0],
                "theta2_deg": theta_deg[1],
                "theta3_deg": theta_deg[2],

                "yaw_deg": np.nan,
                "pitch_deg": np.nan,
                "roll_deg": np.nan,

                "normal_x": np.nan,
                "normal_y": np.nan,
                "normal_z": np.nan,
                "tilt_deg": np.nan,

                "fk_error": np.nan,
                "zeta": 0.0,
                "singular": 1,
                "feasible": 0,
                "message": order_message,
            })
            continue

        R_platform, euler_rad, fk_error, fk_ok = forward_kinematics(
            theta_rad,
            previous_euler_rad,
        )

        if not fk_ok:
            results.append({
                "theta1_deg": theta_deg[0],
                "theta2_deg": theta_deg[1],
                "theta3_deg": theta_deg[2],

                "yaw_deg": np.nan,
                "pitch_deg": np.nan,
                "roll_deg": np.nan,

                "normal_x": np.nan,
                "normal_y": np.nan,
                "normal_z": np.nan,
                "tilt_deg": np.nan,

                "fk_error": fk_error,
                "zeta": 0.0,
                "singular": 1,
                "feasible": 0,
                "message": "fk_failed",
            })
            continue

        pose_jump = rotation_distance(previous_R, R_platform)

        if pose_jump > np.deg2rad(POSE_JUMP_MAX_DEG):
            # 这里虽然正运动学有解，但因为怀疑跳到另一个装配模式，
            # 所以这个点仍然判为不可行。
            # 为了方便分析，仍然记录它算出来的法向量和倾角。
            normal, tilt_deg = platform_normal_and_tilt(R_platform)

            results.append({
                "theta1_deg": theta_deg[0],
                "theta2_deg": theta_deg[1],
                "theta3_deg": theta_deg[2],

                "yaw_deg": np.rad2deg(euler_rad[0]),
                "pitch_deg": np.rad2deg(euler_rad[1]),
                "roll_deg": np.rad2deg(euler_rad[2]),

                "normal_x": normal[0],
                "normal_y": normal[1],
                "normal_z": normal[2],
                "tilt_deg": tilt_deg,

                "fk_error": fk_error,
                "zeta": 0.0,
                "singular": 1,
                "feasible": 0,
                "message": "possible_assembly_mode_jump",
            })
            continue

        J, A, B = compute_jacobian(theta_rad, R_platform)
        zeta = conditioning_index(J)

        normal, tilt_deg = platform_normal_and_tilt(R_platform)

        singular = zeta < ZETA_MIN
        feasible = not singular

        results.append({
            "theta1_deg": theta_deg[0],
            "theta2_deg": theta_deg[1],
            "theta3_deg": theta_deg[2],

            "yaw_deg": np.rad2deg(euler_rad[0]),
            "pitch_deg": np.rad2deg(euler_rad[1]),
            "roll_deg": np.rad2deg(euler_rad[2]),

            "normal_x": normal[0],
            "normal_y": normal[1],
            "normal_z": normal[2],
            "tilt_deg": tilt_deg,

            "fk_error": fk_error,
            "zeta": zeta,
            "singular": int(singular),
            "feasible": int(feasible),
            "message": "ok" if feasible else "singular_or_near_singular",
        })

        # 当前正运动学解作为下一个采样点初值
        previous_euler_rad = euler_rad
        previous_R = R_platform

        if k % 1000 == 0:
            print(f"{k}/{len(points)}")

    df = pd.DataFrame(results)
    df.to_csv(OUTPUT_CSV, index=False)

    print("Saved:", OUTPUT_CSV)
    print("Feasible points:", int(df["feasible"].sum()))

    feasible_df = df[df["feasible"] == 1]

    if len(feasible_df) > 0:
        tilt_min = feasible_df["tilt_deg"].min()
        tilt_max = feasible_df["tilt_deg"].max()
        tilt_mean = feasible_df["tilt_deg"].mean()

        print("Platform normal tilt range among feasible points:")
        print("  min tilt deg:", tilt_min)
        print("  max tilt deg:", tilt_max)
        print("  mean tilt deg:", tilt_mean)

        max_idx = feasible_df["tilt_deg"].idxmax()
        max_row = feasible_df.loc[max_idx]

        print("Max tilt configuration:")
        print("  theta deg:", [
            max_row["theta1_deg"],
            max_row["theta2_deg"],
            max_row["theta3_deg"],
        ])
        print("  yaw pitch roll deg:", [
            max_row["yaw_deg"],
            max_row["pitch_deg"],
            max_row["roll_deg"],
        ])
        print("  platform normal:", [
            max_row["normal_x"],
            max_row["normal_y"],
            max_row["normal_z"],
        ])
        print("  zeta:", max_row["zeta"])

    else:
        print("No feasible points. Cannot compute platform tilt range.")

    return df


# ============================================================
# 9. 生成关节空间凸多面体
# ============================================================

def build_joint_space_polytope(df):
    feasible = df[df["feasible"] == 1]

    theta_deg = feasible[[
        "theta1_deg",
        "theta2_deg",
        "theta3_deg",
    ]].to_numpy()

    if len(theta_deg) < 4:
        print("Feasible points are fewer than 4. Cannot build convex hull.")
        return

    theta_rad = np.deg2rad(theta_deg)

    hull = ConvexHull(theta_rad)

    # ConvexHull equations:
    # a*x + b*y + c*z + d <= 0
    equations = hull.equations

    A_p = equations[:, :3]
    b_p = -equations[:, 3]

    np.savez(
        OUTPUT_POLYTOPE,
        A_p=A_p,
        b_p=b_p,
        theta_points_deg=theta_deg,
        theta_points_rad=theta_rad,
    )

    print("Saved:", OUTPUT_POLYTOPE)
    print("Polytope faces:", len(b_p))


# ============================================================
# 10. 主程序
# ============================================================

def main():
    df = scan_workspace()
    build_joint_space_polytope(df)


if __name__ == "__main__":
    main()
