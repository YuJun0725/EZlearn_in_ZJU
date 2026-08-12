"""Orientation filtering and acceleration-limited motor target generation."""

from __future__ import annotations

import math


Quaternion = tuple[float, float, float, float]


def _normalize_quaternion(q: Quaternion) -> Quaternion:
    length = math.sqrt(sum(value * value for value in q))
    if length < 1.0e-12:
        raise ValueError("zero-length quaternion")
    return tuple(value / length for value in q)


def rpy_to_quaternion(yaw_deg, pitch_deg, roll_deg) -> Quaternion:
    """Convert ZYX Euler angles to a (w, x, y, z) quaternion."""
    yaw, pitch, roll = map(
        lambda value: math.radians(float(value)) / 2.0,
        [yaw_deg, pitch_deg, roll_deg],
    )
    cy, sy = math.cos(yaw), math.sin(yaw)
    cp, sp = math.cos(pitch), math.sin(pitch)
    cr, sr = math.cos(roll), math.sin(roll)
    return _normalize_quaternion(
        (
            cr * cp * cy + sr * sp * sy,
            sr * cp * cy - cr * sp * sy,
            cr * sp * cy + sr * cp * sy,
            cr * cp * sy - sr * sp * cy,
        )
    )


def quaternion_to_rpy(q: Quaternion) -> tuple[float, float, float]:
    """Convert a quaternion to ZYX Euler angles in degrees."""
    w, x, y, z = _normalize_quaternion(q)
    roll = math.atan2(2.0 * (w * x + y * z), 1.0 - 2.0 * (x * x + y * y))
    sin_pitch = max(-1.0, min(1.0, 2.0 * (w * y - z * x)))
    pitch = math.asin(sin_pitch)
    yaw = math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))
    return tuple(map(math.degrees, [yaw, pitch, roll]))


def quaternion_distance_deg(a: Quaternion, b: Quaternion) -> float:
    a = _normalize_quaternion(a)
    b = _normalize_quaternion(b)
    dot = abs(sum(x * y for x, y in zip(a, b)))
    return math.degrees(2.0 * math.acos(max(-1.0, min(1.0, dot))))


def quaternion_slerp(a: Quaternion, b: Quaternion, amount: float) -> Quaternion:
    a = _normalize_quaternion(a)
    b = _normalize_quaternion(b)
    amount = max(0.0, min(1.0, float(amount)))
    dot = sum(x * y for x, y in zip(a, b))
    if dot < 0.0:
        b = tuple(-value for value in b)
        dot = -dot

    dot = max(-1.0, min(1.0, dot))
    if dot > 0.9995:
        return _normalize_quaternion(
            tuple(x + amount * (y - x) for x, y in zip(a, b))
        )

    angle = math.acos(dot)
    sin_angle = math.sin(angle)
    first = math.sin((1.0 - amount) * angle) / sin_angle
    second = math.sin(amount * angle) / sin_angle
    return _normalize_quaternion(
        tuple(first * x + second * y for x, y in zip(a, b))
    )


def _low_pass_alpha(cutoff_hz: float, dt: float) -> float:
    return 1.0 - math.exp(-2.0 * math.pi * cutoff_hz * dt)


class AdaptiveOrientationFilter:
    """Quaternion low-pass filter that opens up during intentional motion."""

    def __init__(
        self,
        min_cutoff_hz: float = 3.0,
        beta: float = 0.025,
        speed_cutoff_hz: float = 1.0,
    ):
        if min_cutoff_hz <= 0.0 or speed_cutoff_hz <= 0.0 or beta < 0.0:
            raise ValueError("invalid adaptive orientation filter settings")
        self.min_cutoff_hz = float(min_cutoff_hz)
        self.beta = float(beta)
        self.speed_cutoff_hz = float(speed_cutoff_hz)
        self.filtered: Quaternion | None = None
        self.previous_raw: Quaternion | None = None
        self.previous_time: float | None = None
        self.filtered_speed_deg_s = 0.0

    def update(self, rpy_deg, timestamp: float) -> tuple[float, float, float]:
        raw = rpy_to_quaternion(*rpy_deg)
        if self.filtered is None or self.previous_raw is None:
            self.filtered = raw
            self.previous_raw = raw
            self.previous_time = float(timestamp)
            return quaternion_to_rpy(self.filtered)

        dt = float(timestamp) - float(self.previous_time)
        dt = max(1.0e-4, min(dt, 0.1))
        raw_speed = quaternion_distance_deg(self.previous_raw, raw) / dt
        speed_alpha = _low_pass_alpha(self.speed_cutoff_hz, dt)
        self.filtered_speed_deg_s += speed_alpha * (
            raw_speed - self.filtered_speed_deg_s
        )

        cutoff = self.min_cutoff_hz + self.beta * self.filtered_speed_deg_s
        orientation_alpha = _low_pass_alpha(cutoff, dt)
        self.filtered = quaternion_slerp(self.filtered, raw, orientation_alpha)
        self.previous_raw = raw
        self.previous_time = float(timestamp)
        return quaternion_to_rpy(self.filtered)


class ThetaMotionLimiter:
    """Generate smooth theta commands with bounded speed and acceleration."""

    def __init__(
        self,
        initial_theta=(0.0, 0.0, 0.0),
        max_speed_deg_s: float = 90.0,
        max_acceleration_deg_s2: float = 360.0,
    ):
        if max_speed_deg_s <= 0.0 or max_acceleration_deg_s2 <= 0.0:
            raise ValueError("theta speed and acceleration limits must be positive")
        if len(initial_theta) != 3:
            raise ValueError("three initial theta values are required")
        self.max_speed = float(max_speed_deg_s)
        self.max_acceleration = float(max_acceleration_deg_s2)
        self.current = [float(value) for value in initial_theta]
        self.target = list(self.current)
        self.velocity = [0.0, 0.0, 0.0]
        self.previous_time: float | None = None

    def set_target(self, theta_deg):
        if len(theta_deg) != 3:
            raise ValueError("three theta target values are required")
        self.target = [float(value) for value in theta_deg]

    def hold(self):
        """Stop the generated trajectory at its current command position."""
        self.target = list(self.current)
        self.velocity = [0.0, 0.0, 0.0]

    def step(self, timestamp: float) -> tuple[tuple[float, float, float], bool]:
        if self.previous_time is None:
            self.previous_time = float(timestamp)
            moving = any(
                abs(target - current) > 1.0e-6
                for target, current in zip(self.target, self.current)
            )
            return tuple(self.current), moving

        dt = max(1.0e-4, min(float(timestamp) - self.previous_time, 0.05))
        self.previous_time = float(timestamp)
        moving = False

        for axis in range(3):
            error = self.target[axis] - self.current[axis]
            if abs(error) < 1.0e-5 and abs(self.velocity[axis]) < 1.0e-4:
                self.current[axis] = self.target[axis]
                self.velocity[axis] = 0.0
                continue

            stopping_speed = math.sqrt(
                max(0.0, 2.0 * self.max_acceleration * abs(error))
            )
            desired_velocity = math.copysign(
                min(self.max_speed, stopping_speed), error
            )
            velocity_change = desired_velocity - self.velocity[axis]
            max_change = self.max_acceleration * dt
            velocity_change = max(-max_change, min(max_change, velocity_change))
            new_velocity = self.velocity[axis] + velocity_change
            position_step = 0.5 * (self.velocity[axis] + new_velocity) * dt

            if position_step * error <= 0.0:
                position_step = 0.0
            if abs(position_step) >= abs(error):
                self.current[axis] = self.target[axis]
            else:
                self.current[axis] += position_step

            self.velocity[axis] = new_velocity
            moving = moving or abs(self.target[axis] - self.current[axis]) > 1.0e-5
            moving = moving or abs(new_velocity) > 1.0e-4

        return tuple(self.current), moving
