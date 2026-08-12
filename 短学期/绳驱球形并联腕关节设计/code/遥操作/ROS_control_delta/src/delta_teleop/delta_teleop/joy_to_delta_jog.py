#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Joy
from geometry_msgs.msg import Twist


class JoyToDeltaJog(Node):
    def __init__(self):
        super().__init__('joy_to_delta_jog')

        self.declare_parameter('deadman_button', 7)

        self.declare_parameter('x_axis', 0)
        self.declare_parameter('y_axis', 1)

        self.declare_parameter('z_up_button', 6)
        self.declare_parameter('z_down_button', 8)

        self.declare_parameter('x_speed', -5.0)  # mm/s
        self.declare_parameter('y_speed', 5.0)   # mm/s
        self.declare_parameter('z_speed', 2.0)   # mm/s
        self.declare_parameter('deadzone', 0.15)

        self.deadman_button = int(self.get_parameter('deadman_button').value)

        self.x_axis = int(self.get_parameter('x_axis').value)
        self.y_axis = int(self.get_parameter('y_axis').value)

        self.z_up_button = int(self.get_parameter('z_up_button').value)
        self.z_down_button = int(self.get_parameter('z_down_button').value)

        self.x_speed = float(self.get_parameter('x_speed').value)
        self.y_speed = float(self.get_parameter('y_speed').value)
        self.z_speed = float(self.get_parameter('z_speed').value)
        self.deadzone = float(self.get_parameter('deadzone').value)

        self.pub = self.create_publisher(Twist, '/delta_jog_cmd', 10)
        self.sub = self.create_subscription(Joy, '/joy', self.on_joy, 10)

        self.get_logger().info('joy_to_delta_jog started')

    def axis_value(self, msg, index):
        if index < 0 or index >= len(msg.axes):
            return 0.0
        value = float(msg.axes[index])
        if abs(value) < self.deadzone:
            return 0.0
        return value

    def button_pressed(self, msg, index):
        if index < 0 or index >= len(msg.buttons):
            return False
        return msg.buttons[index] == 1

    def on_joy(self, msg):
        cmd = Twist()

        if self.button_pressed(msg, self.deadman_button):
            cmd.linear.x = self.axis_value(msg, self.x_axis) * self.x_speed
            cmd.linear.y = self.axis_value(msg, self.y_axis) * self.y_speed

            z = 0.0
            if self.button_pressed(msg, self.z_up_button):
                z += self.z_speed
            if self.button_pressed(msg, self.z_down_button):
                z -= self.z_speed

            cmd.linear.z = z

        self.pub.publish(cmd)


def main(args=None):
    rclpy.init(args=args)
    node = JoyToDeltaJog()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()

