"""Inverse kinematics for one pose of the three-axis spherical wrist."""

from __future__ import annotations

import math
from dataclasses import dataclass


EPS = 1.0e-12


@dataclass(frozen=True)
class WristConfig:
    w0_list: list[list[float]]
    v0_list: list[list[float]]
    working_mode: tuple[int, int, int]
    joint_limits_deg: list[list[float]]
    min_axis_clearance_deg: float
    alpha_deg: list[float | None] | None = None


@dataclass(frozen=True)
class WristSolution:
    theta_deg: tuple[float, float, float]
    residuals: tuple[float, float, float]
    min_axis_gap_deg: float


def _normalize(vector):
    length = math.sqrt(sum(float(value) ** 2 for value in vector))
    if length < EPS:
        raise ValueError("zero-length geometry vector")
    return [float(value) / length for value in vector]


def _dot(a, b):
    return sum(x * y for x, y in zip(a, b))


def _mat_mul(a, b):
    return [
        [sum(a[i][k] * b[k][j] for k in range(3)) for j in range(3)]
        for i in range(3)
    ]


def _mat_vec(matrix, vector):
    return [sum(row[i] * vector[i] for i in range(3)) for row in matrix]


def _rot_x(angle):
    c, s = math.cos(angle), math.sin(angle)
    return [[1.0, 0.0, 0.0], [0.0, c, -s], [0.0, s, c]]


def _rot_y(angle):
    c, s = math.cos(angle), math.sin(angle)
    return [[c, 0.0, s], [0.0, 1.0, 0.0], [-s, 0.0, c]]


def _rot_z(angle):
    c, s = math.cos(angle), math.sin(angle)
    return [[c, -s, 0.0], [s, c, 0.0], [0.0, 0.0, 1.0]]


def rpy_to_rotation(yaw_deg, pitch_deg, roll_deg):
    """Return Rz(yaw) @ Ry(pitch) @ Rx(roll), with angles in degrees."""
    yaw, pitch, roll = map(math.radians, [yaw_deg, pitch_deg, roll_deg])
    return _mat_mul(_mat_mul(_rot_z(yaw), _rot_y(pitch)), _rot_x(roll))


def _wrap_degrees(angle):
    return (angle + 180.0) % 360.0 - 180.0


def _leg_candidates(w0, v0, rotation, alpha_deg):
    w0 = _normalize(w0)
    v0 = _normalize(v0)
    v = _mat_vec(rotation, v0)
    cos_alpha = _dot(w0, v0)
    if alpha_deg is not None:
        cos_alpha = math.cos(math.radians(float(alpha_deg)))

    wx, wy, wz = w0
    vx, vy, vz = v
    a = wx * vx + wy * vy
    b = wx * vy - wy * vx
    c = cos_alpha - wz * vz
    rho = math.hypot(a, b)
    if rho < EPS:
        raise ValueError("rho is too small; this pose is singular")

    q = c / rho
    if abs(q) > 1.0 + 1.0e-10:
        raise ValueError(f"pose has no inverse solution: abs(C/rho)={abs(q):.8f}")
    q = max(-1.0, min(1.0, q))

    phi = math.atan2(b, a)
    delta = math.acos(q)
    return {
        1: _wrap_degrees(math.degrees(phi + delta)),
        -1: _wrap_degrees(math.degrees(phi - delta)),
    }


def _constraint_residual(w0, v0, rotation, theta_deg, alpha_deg):
    w0 = _normalize(w0)
    v0 = _normalize(v0)
    w = _mat_vec(_rot_z(math.radians(theta_deg)), w0)
    v = _mat_vec(rotation, v0)
    cos_alpha = _dot(w0, v0)
    if alpha_deg is not None:
        cos_alpha = math.cos(math.radians(float(alpha_deg)))
    return _dot(w, v) - cos_alpha


def _check_axis_order(w0_list, theta_deg, clearance_deg):
    base_azimuths = [math.atan2(w[1], w[0]) for w in w0_list]
    if any(math.hypot(w[0], w[1]) < EPS for w in w0_list):
        raise ValueError("w0 contains an axis without a defined azimuth")

    order = sorted(range(3), key=base_azimuths.__getitem__)
    current = [
        (base + math.radians(theta)) % (2.0 * math.pi)
        for base, theta in zip(base_azimuths, theta_deg)
    ]
    gaps = [
        (current[order[(i + 1) % 3]] - current[order[i]]) % (2.0 * math.pi)
        for i in range(3)
    ]
    if not math.isclose(sum(gaps), 2.0 * math.pi, abs_tol=1.0e-9):
        raise ValueError("axis circular order changed; target is unsafe")
    min_gap = math.degrees(min(gaps))
    if min_gap <= float(clearance_deg) + 1.0e-9:
        raise ValueError(
            f"axis gap {min_gap:.3f} deg is below the configured "
            f"{float(clearance_deg):.3f} deg clearance"
        )
    return min_gap


def validate_theta_target(theta_deg, config: WristConfig):
    """Validate limits, circular branch order, and branch clearance."""
    if len(theta_deg) != 3:
        raise ValueError("exactly three theta values are required")
    for index, (angle, limits) in enumerate(
        zip(theta_deg, config.joint_limits_deg), start=1
    ):
        lower, upper = map(float, limits)
        if not lower <= float(angle) <= upper:
            raise ValueError(
                f"theta{index}={float(angle):.3f} deg is outside "
                f"[{lower:.3f}, {upper:.3f}] deg"
            )
    return _check_axis_order(
        config.w0_list, theta_deg, config.min_axis_clearance_deg
    )


def solve_wrist_rpy(yaw_deg, pitch_deg, roll_deg, config: WristConfig):
    if len(config.w0_list) != 3 or len(config.v0_list) != 3:
        raise ValueError("exactly three w0 vectors and three v0 vectors are required")
    if len(config.working_mode) != 3 or any(
        mode not in (-1, 1) for mode in config.working_mode
    ):
        raise ValueError("working_mode must contain three +1/-1 values")

    alpha = config.alpha_deg or [None, None, None]
    if len(alpha) != 3:
        raise ValueError("alpha_deg must contain three values")

    rotation = rpy_to_rotation(yaw_deg, pitch_deg, roll_deg)
    theta = []
    residuals = []
    for index in range(3):
        candidates = _leg_candidates(
            config.w0_list[index],
            config.v0_list[index],
            rotation,
            alpha[index],
        )
        angle = candidates[config.working_mode[index]]
        theta.append(angle)
        residuals.append(
            _constraint_residual(
                config.w0_list[index],
                config.v0_list[index],
                rotation,
                angle,
                alpha[index],
            )
        )

    min_gap = validate_theta_target(theta, config)
    return WristSolution(tuple(theta), tuple(residuals), min_gap)
