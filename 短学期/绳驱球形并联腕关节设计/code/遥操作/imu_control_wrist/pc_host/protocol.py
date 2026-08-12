"""Binary serial protocol shared by the PC host and ESP32 firmware."""

from __future__ import annotations

import struct
from dataclasses import dataclass


SOF = 0xAA55
TYPE_ACK = 0x02
TYPE_SET_WRIST_TARGET = 0x20
TYPE_SENSOR_STATUS = 0x30
TYPE_IMU_RPY = 0x31

HEADER = struct.Struct("<HBHH")
CRC_FIELD = struct.Struct("<H")
THREE_ANGLES = struct.Struct("<iii")
MAX_PAYLOAD_LENGTH = 32


@dataclass(frozen=True)
class Frame:
    message_type: int
    sequence: int
    payload: bytes


def crc16_ccitt_false(data: bytes) -> int:
    crc = 0xFFFF
    for byte in data:
        crc ^= byte << 8
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc


def encode_frame(message_type: int, sequence: int, payload: bytes = b"") -> bytes:
    if len(payload) > MAX_PAYLOAD_LENGTH:
        raise ValueError("payload is too long")
    body = struct.pack(
        "<BHH", message_type, sequence & 0xFFFF, len(payload)
    ) + payload
    return struct.pack("<H", SOF) + body + CRC_FIELD.pack(crc16_ccitt_false(body))


def _pack_three_angles_deg(angles_deg) -> bytes:
    values = tuple(float(value) for value in angles_deg)
    if len(values) != 3:
        raise ValueError("exactly three angles are required")
    millidegrees = tuple(round(value * 1000.0) for value in values)
    if any(not -(2**31) <= value < 2**31 for value in millidegrees):
        raise ValueError("angle cannot be represented as int32 millidegrees")
    return THREE_ANGLES.pack(*millidegrees)


def pack_wrist_target(theta_deg) -> bytes:
    return _pack_three_angles_deg(theta_deg)


def unpack_imu_rpy(payload: bytes) -> tuple[float, float, float]:
    if len(payload) != THREE_ANGLES.size:
        raise ValueError("invalid IMU RPY payload length")
    return tuple(value / 1000.0 for value in THREE_ANGLES.unpack(payload))


def unpack_ack(payload: bytes) -> tuple[int, int]:
    if len(payload) != 2:
        raise ValueError("invalid ACK payload length")
    return struct.unpack("<BB", payload)


def unpack_sensor_status(payload: bytes) -> tuple[int, int]:
    if len(payload) != 2:
        raise ValueError("invalid sensor status payload length")
    return struct.unpack("<BB", payload)


class FrameDecoder:
    def __init__(self):
        self.buffer = bytearray()

    def feed(self, data: bytes) -> list[Frame]:
        self.buffer.extend(data)
        frames = []
        sof = struct.pack("<H", SOF)

        while True:
            start = self.buffer.find(sof)
            if start < 0:
                self.buffer[:] = self.buffer[-1:]
                break
            if start:
                del self.buffer[:start]
            if len(self.buffer) < HEADER.size:
                break

            _, message_type, sequence, payload_length = HEADER.unpack_from(self.buffer)
            if payload_length > MAX_PAYLOAD_LENGTH:
                del self.buffer[0]
                continue

            frame_length = HEADER.size + payload_length + CRC_FIELD.size
            if len(self.buffer) < frame_length:
                break

            body_end = HEADER.size + payload_length
            body = bytes(self.buffer[2:body_end])
            received_crc = CRC_FIELD.unpack_from(self.buffer, body_end)[0]
            if crc16_ccitt_false(body) != received_crc:
                del self.buffer[0]
                continue

            payload = bytes(self.buffer[HEADER.size:body_end])
            frames.append(Frame(message_type, sequence, payload))
            del self.buffer[:frame_length]

        return frames

