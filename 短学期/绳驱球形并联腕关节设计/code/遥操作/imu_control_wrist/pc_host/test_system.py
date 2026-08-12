from __future__ import annotations

import unittest
from pathlib import Path

from main import load_config
from protocol import (
    TYPE_IMU_RPY,
    FrameDecoder,
    crc16_ccitt_false,
    encode_frame,
    unpack_imu_rpy,
)
from smoothing import (
    AdaptiveOrientationFilter,
    ThetaMotionLimiter,
    quaternion_distance_deg,
    rpy_to_quaternion,
)
from solver import _check_axis_order, solve_wrist_rpy


HERE = Path(__file__).resolve().parent


class ProtocolTests(unittest.TestCase):
    def test_standard_crc_vector(self):
        self.assertEqual(crc16_ccitt_false(b"123456789"), 0x29B1)

    def test_decoder_accepts_fragmented_frame(self):
        payload = bytes.fromhex("20 4e 00 00 30 f8 ff ff 00 00 00 00")
        encoded = encode_frame(TYPE_IMU_RPY, 42, payload)
        decoder = FrameDecoder()
        frames = []
        for chunk in (encoded[:3], encoded[3:8], encoded[8:]):
            frames.extend(decoder.feed(chunk))
        self.assertEqual(len(frames), 1)
        self.assertEqual(frames[0].sequence, 42)
        self.assertEqual(unpack_imu_rpy(frames[0].payload), (20.0, -2.0, 0.0))


class SolverTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.config = load_config(HERE / "config.json")

    def test_home_pose_maps_to_zero_theta(self):
        solution = solve_wrist_rpy(0.0, 0.0, 0.0, self.config)
        for theta in solution.theta_deg:
            self.assertAlmostEqual(theta, 0.0, places=8)
        for residual in solution.residuals:
            self.assertAlmostEqual(residual, 0.0, places=10)

    def test_nonzero_pose_satisfies_constraints(self):
        solution = solve_wrist_rpy(20.0, 20.0, 30.0, self.config)
        self.assertGreater(solution.min_axis_gap_deg, 5.0)
        for residual in solution.residuals:
            self.assertAlmostEqual(residual, 0.0, places=10)

    def test_changed_circular_order_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "circular order changed"):
            _check_axis_order(
                self.config.w0_list,
                [120.0, -120.0, 0.0],
                self.config.min_axis_clearance_deg,
            )


class SmoothingTests(unittest.TestCase):
    def test_orientation_filter_crosses_yaw_wrap_without_large_jump(self):
        orientation_filter = AdaptiveOrientationFilter()
        first = orientation_filter.update((179.0, 0.0, 0.0), 0.0)
        second = orientation_filter.update((-179.0, 0.0, 0.0), 0.01)
        distance = quaternion_distance_deg(
            rpy_to_quaternion(*first), rpy_to_quaternion(*second)
        )
        self.assertLess(distance, 2.0)

    def test_theta_motion_is_bounded_and_reaches_target(self):
        limiter = ThetaMotionLimiter(
            max_speed_deg_s=90.0,
            max_acceleration_deg_s2=360.0,
        )
        limiter.set_target((30.0, -20.0, 10.0))
        limiter.step(0.0)
        previous_velocity = tuple(limiter.velocity)
        for index in range(1, 301):
            current, moving = limiter.step(index * 0.02)
            self.assertLessEqual(max(map(abs, limiter.velocity)), 90.0 + 1.0e-9)
            acceleration = max(
                abs(now - before) / 0.02
                for now, before in zip(limiter.velocity, previous_velocity)
            )
            self.assertLessEqual(acceleration, 360.0 + 1.0e-7)
            previous_velocity = tuple(limiter.velocity)
            if not moving:
                break
        for actual, expected in zip(current, (30.0, -20.0, 10.0)):
            self.assertAlmostEqual(actual, expected, places=6)


if __name__ == "__main__":
    unittest.main()
