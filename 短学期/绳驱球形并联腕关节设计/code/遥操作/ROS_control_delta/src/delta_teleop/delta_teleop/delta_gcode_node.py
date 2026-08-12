#!/usr/bin/env python3

import time

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist

try:
    import serial
except ImportError:
    serial = None


class DeltaGcodeNode(Node):
    def __init__(self):
        super().__init__('delta_gcode_node')

        self.declare_parameter('serial_port', '/dev/ttyACM0')
        self.declare_parameter('baudrate', 115200)
        self.declare_parameter('dry_run', True)

        self.declare_parameter('min_feedrate_mm_min', 100.0)
        self.declare_parameter('max_feedrate_mm_min', 2000.0)


        self.declare_parameter('rate_hz', 5.0)
        self.declare_parameter('max_step_mm', 1.0)
        self.declare_parameter('feedrate_mm_min', 300.0)
        self.declare_parameter('command_timeout_s', 0.5)
        self.declare_parameter('ok_timeout_s', 3.0)

        self.serial_port = str(self.get_parameter('serial_port').value)
        self.baudrate = int(self.get_parameter('baudrate').value)
        self.dry_run = bool(self.get_parameter('dry_run').value)

        self.min_feedrate_mm_min = float(
        self.get_parameter('min_feedrate_mm_min').value
        )
        self.max_feedrate_mm_min = float(
        self.get_parameter('max_feedrate_mm_min').value
        )


        self.rate_hz = float(self.get_parameter('rate_hz').value)
        self.period = 1.0 / self.rate_hz
        self.max_step_mm = float(self.get_parameter('max_step_mm').value)
        self.feedrate_mm_min = float(self.get_parameter('feedrate_mm_min').value)
        self.command_timeout_s = float(self.get_parameter('command_timeout_s').value)
        self.ok_timeout_s = float(self.get_parameter('ok_timeout_s').value)

        self.last_cmd = Twist()
        self.last_cmd_time = self.get_clock().now()
        self.ser = None

        if self.dry_run:
            self.get_logger().warn('dry_run=true, only printing G-code')
        else:
            if serial is None:
                raise RuntimeError('python3-serial is not installed')
            self.ser = serial.Serial(self.serial_port, self.baudrate, timeout=0.1)
            time.sleep(2.0)
            self.ser.reset_input_buffer()
            self.get_logger().info(
                f'Opened serial port {self.serial_port} at {self.baudrate}'
            )
            self.send_line('M115')

        self.sub = self.create_subscription(
            Twist,
            '/delta_jog_cmd',
            self.on_cmd,
            10,
        )
        self.timer = self.create_timer(self.period, self.on_timer)

        self.get_logger().info('delta_gcode_node started')

    def on_cmd(self, msg):
        self.last_cmd = msg
        self.last_cmd_time = self.get_clock().now()

    def clip(self, value, limit):
        return max(-limit, min(limit, value))

    def on_timer(self):
        now = self.get_clock().now()
        age = (now - self.last_cmd_time).nanoseconds / 1e9

        if age > self.command_timeout_s:
            return

        dx = self.clip(self.last_cmd.linear.x * self.period, self.max_step_mm)
        dy = self.clip(self.last_cmd.linear.y * self.period, self.max_step_mm)
        dz = self.clip(self.last_cmd.linear.z * self.period, self.max_step_mm)

        speed_mm_s = math.sqrt(
        self.last_cmd.linear.x ** 2 +
        self.last_cmd.linear.y ** 2 +
        self.last_cmd.linear.z ** 2
        )

        feedrate = speed_mm_s * 60.0
        feedrate = max(self.min_feedrate_mm_min, feedrate)
        feedrate = min(self.max_feedrate_mm_min, feedrate)


        if max(abs(dx), abs(dy), abs(dz)) < 0.001:
            return

        self.send_line('G91')
        self.send_line(
            f'G1 X{dx:.3f} Y{dy:.3f} Z{dz:.3f} F{feedrate:.0f}'
        )

        # self.send_line('M400')
        # self.send_line('G90')

    def send_line(self, line):
        line = line.strip()
        self.get_logger().info(f'GCODE: {line}')

        if self.ser is None:
            return

        self.ser.write((line + '\n').encode('ascii'))
        self.ser.flush()

        deadline = time.time() + self.ok_timeout_s
        while time.time() < deadline:
            reply = self.ser.readline().decode(errors='ignore').strip()
            if not reply:
                continue

            self.get_logger().debug(f'PRINTER: {reply}')

            if reply.lower().startswith('ok'):
                return

            if 'error' in reply.lower():
                self.get_logger().error(f'Printer error: {reply}')
                return

        self.get_logger().warn(f'No ok from printer after: {line}')


def main(args=None):
    rclpy.init(args=args)
    node = DeltaGcodeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
