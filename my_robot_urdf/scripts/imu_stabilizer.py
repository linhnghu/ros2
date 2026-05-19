#!/usr/bin/env python3

import math

import rclpy
from rclpy.node import Node
from rclpy.qos import HistoryPolicy, QoSProfile, ReliabilityPolicy
from sensor_msgs.msg import Imu


class ImuStabilizer(Node):
    def __init__(self):
        super().__init__('imu_stabilizer')

        self.declare_parameter('input_topic', '/imu/data')
        self.declare_parameter('output_topic', '/imu/cartographer')
        self.declare_parameter('frame_id', 'base_link')
        self.declare_parameter('gravity', 9.80665)

        input_topic = self.get_parameter('input_topic').value
        output_topic = self.get_parameter('output_topic').value
        self.frame_id = self.get_parameter('frame_id').value
        self.gravity = float(self.get_parameter('gravity').value)

        qos = QoSProfile(
            history=HistoryPolicy.KEEP_LAST,
            depth=200,
            reliability=ReliabilityPolicy.BEST_EFFORT,
        )

        self.publisher = self.create_publisher(Imu, output_topic, qos)
        self.subscription = self.create_subscription(
            Imu,
            input_topic,
            self.imu_callback,
            qos,
        )

        self.get_logger().info(
            f'Stabilizing IMU from {input_topic} to {output_topic} in {self.frame_id}'
        )

    def imu_callback(self, raw_msg):
        msg = Imu()
        msg.header = raw_msg.header
        msg.header.frame_id = self.frame_id

        # SLAM preintegration is sensitive to tiny horizontal accelerations while
        # this robot is planar. Keep yaw and vertical gravity, then remove roll,
        # pitch, and horizontal acceleration from the SLAM IMU stream.
        yaw = self._yaw_from_quaternion(raw_msg.orientation)
        msg.orientation.z = math.sin(yaw * 0.5)
        msg.orientation.w = math.cos(yaw * 0.5)
        msg.orientation_covariance[0] = 1e-4
        msg.orientation_covariance[4] = 1e-4
        msg.orientation_covariance[8] = 1e-4

        msg.angular_velocity.x = 0.0
        msg.angular_velocity.y = 0.0
        msg.angular_velocity.z = raw_msg.angular_velocity.z
        msg.angular_velocity_covariance[0] = 1e-4
        msg.angular_velocity_covariance[4] = 1e-4
        msg.angular_velocity_covariance[8] = 1e-4

        msg.linear_acceleration.x = 0.0
        msg.linear_acceleration.y = 0.0
        msg.linear_acceleration.z = self.gravity
        msg.linear_acceleration_covariance[0] = 1e-3
        msg.linear_acceleration_covariance[4] = 1e-3
        msg.linear_acceleration_covariance[8] = 1e-3

        self.publisher.publish(msg)

    @staticmethod
    def _yaw_from_quaternion(quaternion):
        norm = math.sqrt(
            quaternion.x * quaternion.x
            + quaternion.y * quaternion.y
            + quaternion.z * quaternion.z
            + quaternion.w * quaternion.w
        )
        if norm < 1e-6:
            return 0.0

        x = quaternion.x / norm
        y = quaternion.y / norm
        z = quaternion.z / norm
        w = quaternion.w / norm
        return math.atan2(2.0 * (w * z + x * y), 1.0 - 2.0 * (y * y + z * z))


def main(args=None):
    rclpy.init(args=args)
    node = ImuStabilizer()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
