#!/usr/bin/env python3
"""Receive IMU RPY from ESP32, solve theta, and send servo targets back."""

from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from protocol import (
    TYPE_ACK,
    TYPE_IMU_RPY,
    TYPE_SENSOR_STATUS,
    TYPE_SET_WRIST_TARGET,
    FrameDecoder,
    encode_frame,
    pack_wrist_target,
    unpack_ack,
    unpack_imu_rpy,
    unpack_sensor_status,
)
from smoothing import (
    AdaptiveOrientationFilter,
    ThetaMotionLimiter,
    quaternion_distance_deg,
    rpy_to_quaternion,
)
from solver import WristConfig, solve_wrist_rpy, validate_theta_target


HERE = Path(__file__).resolve().parent
ACK_STATUS_TEXT = {
    0: "accepted",
    1: "bad payload length",
    2: "unsupported message type",
    3: "target outside servo limits",
    4: "axis circular order or clearance is unsafe",
}
SENSOR_STATUS_TEXT = {
    0: "no response",
    1: "responding",
    2: "bus error",
    3: "keep the controller still during calibration",
}


def load_config(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    wrist = WristConfig(
        w0_list=data["w0_list"],
        v0_list=data["v0_list"],
        alpha_deg=data.get("alpha_deg"),
        working_mode=tuple(data.get("working_mode", [1, 1, 1])),
        joint_limits_deg=data.get("joint_limits_deg", [[-120, 120]] * 3),
        min_axis_clearance_deg=float(data.get("min_axis_clearance_deg", 5.0)),
    )
    return data, wrist


def list_serial_ports():
    try:
        from serial.tools import list_ports
    except ImportError as exc:
        raise RuntimeError(
            "pyserial is required; run: python -m pip install -r requirements.txt"
        ) from exc

    ports = list(list_ports.comports())
    if not ports:
        print("No serial ports found")
        return
    for port in ports:
        print(f"{port.device}: {port.description}")


def open_serial(port, baudrate, startup_delay):
    try:
        import serial
    except ImportError as exc:
        raise RuntimeError(
            "pyserial is required; run: python -m pip install -r requirements.txt"
        ) from exc

    connection = serial.Serial(
        port=port,
        baudrate=baudrate,
        timeout=0.02,
        write_timeout=1.0,
    )
    if startup_delay > 0:
        time.sleep(startup_delay)
    return connection


class RealtimeController:
    def __init__(self, connection, wrist_config, settings, monitor_only=False):
        self.connection = connection
        self.wrist_config = wrist_config
        self.decoder = FrameDecoder()
        self.monitor_only = monitor_only
        self.command_period = 1.0 / float(settings.get("command_rate_hz", 50.0))
        self.display_period = 1.0 / float(settings.get("display_rate_hz", 5.0))
        self.ack_timeout = float(settings.get("ack_timeout_s", 1.0))
        self.orientation_deadband = float(
            settings.get("orientation_deadband_deg", 0.1)
        )
        self.command_epsilon = float(
            settings.get("theta_command_epsilon_deg", 0.005)
        )
        self.orientation_filter = AdaptiveOrientationFilter(
            min_cutoff_hz=float(
                settings.get("orientation_filter_min_cutoff_hz", 5.0)
            ),
            beta=float(settings.get("orientation_filter_beta", 0.05)),
            speed_cutoff_hz=float(
                settings.get("orientation_speed_cutoff_hz", 1.0)
            ),
        )
        self.motion_limiter = ThetaMotionLimiter(
            initial_theta=(0.0, 0.0, 0.0),
            max_speed_deg_s=float(settings.get("theta_max_speed_deg_s", 200.0)),
            max_acceleration_deg_s2=float(
                settings.get("theta_max_acceleration_deg_s2", 1300.0)
            ),
        )
        self.target_sequence = 0
        self.last_control_time = 0.0
        self.last_display_time = 0.0
        self.last_rpy_time = None
        self.last_error = None
        self.pending_acks = {}
        self.raw_rpy = None
        self.filtered_rpy = None
        self.accepted_orientation = None
        self.target_theta = (0.0, 0.0, 0.0)
        self.target_gap = 120.0
        self.last_sent_theta = None

    def _next_sequence(self):
        self.target_sequence = (self.target_sequence + 1) & 0xFFFF
        return self.target_sequence

    def send_target(self, theta_deg):
        sequence = self._next_sequence()
        frame = encode_frame(
            TYPE_SET_WRIST_TARGET, sequence, pack_wrist_target(theta_deg)
        )
        self.connection.write(frame)
        self.pending_acks[sequence] = time.monotonic()

    def _handle_rpy(self, frame, now):
        self.raw_rpy = unpack_imu_rpy(frame.payload)
        self.filtered_rpy = self.orientation_filter.update(self.raw_rpy, now)
        self.last_rpy_time = now

    def _update_inverse_target(self):
        if self.filtered_rpy is None:
            return

        orientation = rpy_to_quaternion(*self.filtered_rpy)
        if self.accepted_orientation is not None:
            change = quaternion_distance_deg(self.accepted_orientation, orientation)
            if change < self.orientation_deadband:
                return

        try:
            solution = solve_wrist_rpy(*self.filtered_rpy, self.wrist_config)
        except ValueError as exc:
            message = str(exc)
            if message != self.last_error:
                values = ", ".join(f"{value:.3f}" for value in self.filtered_rpy)
                print(f"REJECT filtered RPY [{values}]: {message}")
                self.last_error = message
            return

        self.last_error = None
        self.accepted_orientation = orientation
        self.target_theta = solution.theta_deg
        self.target_gap = solution.min_axis_gap_deg
        self.motion_limiter.set_target(solution.theta_deg)

    def _service_control(self, now):
        if self.filtered_rpy is None:
            return
        if now - self.last_control_time < self.command_period:
            return
        self.last_control_time = now
        self._update_inverse_target()

        theta_command, _ = self.motion_limiter.step(now)
        try:
            command_gap = validate_theta_target(theta_command, self.wrist_config)
        except ValueError as exc:
            self.motion_limiter.hold()
            message = f"generated theta rejected: {exc}"
            if message != self.last_error:
                print(f"SAFETY STOP: {message}")
                self.last_error = message
            return

        changed = self.last_sent_theta is None or max(
            abs(current - previous)
            for current, previous in zip(theta_command, self.last_sent_theta)
        ) >= self.command_epsilon
        if changed:
            if not self.monitor_only:
                self.send_target(theta_command)
            self.last_sent_theta = theta_command

        if now - self.last_display_time >= self.display_period:
            mode = "monitor" if self.monitor_only else "sent"
            raw_text = ", ".join(f"{value:7.2f}" for value in self.raw_rpy)
            filtered_text = ", ".join(
                f"{value:7.2f}" for value in self.filtered_rpy
            )
            target_text = ", ".join(f"{value:7.2f}" for value in self.target_theta)
            command_text = ", ".join(f"{value:7.2f}" for value in theta_command)
            print(
                f"RPY raw [{raw_text}] filtered [{filtered_text}] -> "
                f"theta target [{target_text}] command [{command_text}], "
                f"gap={command_gap:.2f}, {mode}"
            )
            self.last_display_time = now

    def _handle_ack(self, frame):
        original_type, status = unpack_ack(frame.payload)
        self.pending_acks.pop(frame.sequence, None)
        if original_type != TYPE_SET_WRIST_TARGET or status != 0:
            status_text = ACK_STATUS_TEXT.get(status, f"unknown status {status}")
            print(
                f"ESP32 rejected sequence {frame.sequence}: "
                f"type=0x{original_type:02X}, {status_text}"
            )

    @staticmethod
    def _handle_sensor_status(frame):
        sensor_id, status = unpack_sensor_status(frame.payload)
        print(
            f"sensor {sensor_id}: "
            f"{SENSOR_STATUS_TEXT.get(status, f'unknown status {status}') }"
        )

    def _check_ack_timeouts(self, now):
        expired = [
            sequence
            for sequence, sent_at in self.pending_acks.items()
            if now - sent_at > self.ack_timeout
        ]
        for sequence in expired:
            del self.pending_acks[sequence]
            print(f"WARNING: target sequence {sequence} ACK timeout")

    def run(self):
        rate = round(1.0 / self.command_period)
        print(f"Smooth realtime loop started at {rate} Hz; press Ctrl+C to stop")
        while True:
            data = self.connection.read(512)
            now = time.monotonic()
            latest_rpy_frame = None
            for frame in self.decoder.feed(data):
                try:
                    if frame.message_type == TYPE_IMU_RPY:
                        latest_rpy_frame = frame
                    elif frame.message_type == TYPE_ACK:
                        self._handle_ack(frame)
                    elif frame.message_type == TYPE_SENSOR_STATUS:
                        self._handle_sensor_status(frame)
                except ValueError as exc:
                    print(f"Ignored malformed frame: {exc}")
            if latest_rpy_frame is not None:
                try:
                    self._handle_rpy(latest_rpy_frame, now)
                except ValueError as exc:
                    print(f"Ignored malformed IMU frame: {exc}")
            self._service_control(now)
            self._check_ack_timeouts(now)


def send_one_pose(connection, wrist_config, pose, ack_timeout):
    solution = solve_wrist_rpy(*pose, wrist_config)
    sequence = 1
    frame = encode_frame(
        TYPE_SET_WRIST_TARGET, sequence, pack_wrist_target(solution.theta_deg)
    )
    connection.write(frame)
    print(
        "RPY:",
        [round(value, 6) for value in pose],
        "deg -> theta:",
        [round(value, 6) for value in solution.theta_deg],
        "deg",
    )

    decoder = FrameDecoder()
    deadline = time.monotonic() + ack_timeout
    while time.monotonic() < deadline:
        for response in decoder.feed(connection.read(512)):
            if response.message_type != TYPE_ACK or response.sequence != sequence:
                continue
            original_type, status = unpack_ack(response.payload)
            if original_type != TYPE_SET_WRIST_TARGET or status != 0:
                text = ACK_STATUS_TEXT.get(status, f"unknown status {status}")
                raise RuntimeError(f"ESP32 rejected the target: {text}")
            print("ESP32 accepted the target")
            return
    raise TimeoutError("ESP32 ACK timeout")


def build_parser():
    parser = argparse.ArgumentParser(
        description="Use ESP32 IMU RPY as the wrist target pose"
    )
    parser.add_argument("--port", help="COM5 on Windows or /dev/ttyUSB0 on Linux")
    parser.add_argument("--baud", type=int, help="override config serial baudrate")
    parser.add_argument("--config", type=Path, default=HERE / "config.json")
    parser.add_argument("--list-ports", action="store_true")
    parser.add_argument(
        "--monitor-only",
        action="store_true",
        help="solve and print incoming RPY without moving the servos",
    )
    parser.add_argument(
        "--pose",
        nargs=3,
        type=float,
        metavar=("YAW", "PITCH", "ROLL"),
        help="send one manually supplied pose instead of using live IMU data",
    )
    return parser


def main():
    args = build_parser().parse_args()
    if args.list_ports:
        list_serial_ports()
        return
    if not args.port:
        raise SystemExit("--port is required; use --list-ports to find it")

    settings, wrist_config = load_config(args.config)
    baudrate = args.baud or int(settings.get("serial_baudrate", 115200))
    startup_delay = float(settings.get("startup_delay_s", 2.0))
    connection = open_serial(args.port, baudrate, startup_delay)
    try:
        print(f"Opened {args.port} at {baudrate} baud")
        if args.pose is not None:
            send_one_pose(
                connection,
                wrist_config,
                tuple(args.pose),
                float(settings.get("ack_timeout_s", 1.0)),
            )
        else:
            RealtimeController(
                connection, wrist_config, settings, args.monitor_only
            ).run()
    except KeyboardInterrupt:
        print("\nStopped")
    finally:
        connection.close()


if __name__ == "__main__":
    main()
