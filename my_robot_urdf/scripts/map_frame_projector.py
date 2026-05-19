#!/usr/bin/env python3

import math

import rclpy
from geometry_msgs.msg import TransformStamped
from rclpy.node import Node
from rclpy.time import Time
from tf2_ros import Buffer, TransformBroadcaster, TransformException, TransformListener


def normalize_quaternion(q):
    x, y, z, w = q
    norm = math.sqrt(x * x + y * y + z * z + w * w)
    if norm == 0.0:
        return 0.0, 0.0, 0.0, 1.0
    return x / norm, y / norm, z / norm, w / norm


def quaternion_to_matrix(q):
    x, y, z, w = normalize_quaternion(q)
    xx = x * x
    yy = y * y
    zz = z * z
    xy = x * y
    xz = x * z
    yz = y * z
    wx = w * x
    wy = w * y
    wz = w * z

    return [
        [1.0 - 2.0 * (yy + zz), 2.0 * (xy - wz), 2.0 * (xz + wy)],
        [2.0 * (xy + wz), 1.0 - 2.0 * (xx + zz), 2.0 * (yz - wx)],
        [2.0 * (xz - wy), 2.0 * (yz + wx), 1.0 - 2.0 * (xx + yy)],
    ]


def matrix_to_quaternion(m):
    trace = m[0][0] + m[1][1] + m[2][2]
    if trace > 0.0:
        s = math.sqrt(trace + 1.0) * 2.0
        w = 0.25 * s
        x = (m[2][1] - m[1][2]) / s
        y = (m[0][2] - m[2][0]) / s
        z = (m[1][0] - m[0][1]) / s
    elif m[0][0] > m[1][1] and m[0][0] > m[2][2]:
        s = math.sqrt(1.0 + m[0][0] - m[1][1] - m[2][2]) * 2.0
        w = (m[2][1] - m[1][2]) / s
        x = 0.25 * s
        y = (m[0][1] + m[1][0]) / s
        z = (m[0][2] + m[2][0]) / s
    elif m[1][1] > m[2][2]:
        s = math.sqrt(1.0 + m[1][1] - m[0][0] - m[2][2]) * 2.0
        w = (m[0][2] - m[2][0]) / s
        x = (m[0][1] + m[1][0]) / s
        y = 0.25 * s
        z = (m[1][2] + m[2][1]) / s
    else:
        s = math.sqrt(1.0 + m[2][2] - m[0][0] - m[1][1]) * 2.0
        w = (m[1][0] - m[0][1]) / s
        x = (m[0][2] + m[2][0]) / s
        y = (m[1][2] + m[2][1]) / s
        z = 0.25 * s

    return normalize_quaternion((x, y, z, w))


def yaw_from_quaternion(q):
    x, y, z, w = normalize_quaternion(q)
    return math.atan2(
        2.0 * (w * z + x * y),
        1.0 - 2.0 * (y * y + z * z),
    )


def yaw_matrix(yaw):
    cos_yaw = math.cos(yaw)
    sin_yaw = math.sin(yaw)
    return [
        [cos_yaw, -sin_yaw, 0.0],
        [sin_yaw, cos_yaw, 0.0],
        [0.0, 0.0, 1.0],
    ]


def mat_mul(a, b):
    return [
        [
            a[row][0] * b[0][col]
            + a[row][1] * b[1][col]
            + a[row][2] * b[2][col]
            for col in range(3)
        ]
        for row in range(3)
    ]


def mat_vec_mul(m, v):
    return [
        m[0][0] * v[0] + m[0][1] * v[1] + m[0][2] * v[2],
        m[1][0] * v[0] + m[1][1] * v[1] + m[1][2] * v[2],
        m[2][0] * v[0] + m[2][1] * v[1] + m[2][2] * v[2],
    ]


def mat_transpose(m):
    return [
        [m[0][0], m[1][0], m[2][0]],
        [m[0][1], m[1][1], m[2][1]],
        [m[0][2], m[1][2], m[2][2]],
    ]


def compose(transform_a, transform_b):
    rot_a, trans_a = transform_a
    rot_b, trans_b = transform_b
    rot = mat_mul(rot_a, rot_b)
    rotated_trans_b = mat_vec_mul(rot_a, trans_b)
    trans = [
        rotated_trans_b[0] + trans_a[0],
        rotated_trans_b[1] + trans_a[1],
        rotated_trans_b[2] + trans_a[2],
    ]
    return rot, trans


def invert(transform):
    rot, trans = transform
    inv_rot = mat_transpose(rot)
    inv_trans = mat_vec_mul(inv_rot, [-trans[0], -trans[1], -trans[2]])
    return inv_rot, inv_trans


class MapFrameProjector(Node):
    def __init__(self):
        super().__init__('map_frame_projector')

        self.declare_parameter('target_map_frame', 'map')
        self.declare_parameter('source_map_frame', 'cartographer_map')
        self.declare_parameter('robot_frame', 'base_footprint')
        self.declare_parameter('publish_period_sec', 0.02)
        self.declare_parameter('target_z', 0.0)

        self.target_map_frame = self.get_parameter('target_map_frame').value
        self.source_map_frame = self.get_parameter('source_map_frame').value
        self.robot_frame = self.get_parameter('robot_frame').value
        self.target_z = float(self.get_parameter('target_z').value)

        publish_period_sec = float(self.get_parameter('publish_period_sec').value)

        self.tf_buffer = Buffer()
        self.tf_listener = TransformListener(self.tf_buffer, self)
        self.tf_broadcaster = TransformBroadcaster(self)
        self.timer = self.create_timer(publish_period_sec, self.publish_projected_frame)

        self.get_logger().info(
            f'Projecting {self.source_map_frame}->{self.robot_frame} into '
            f'{self.target_map_frame}->{self.robot_frame}'
        )

    def publish_projected_frame(self):
        try:
            transform_msg = self.tf_buffer.lookup_transform(
                self.source_map_frame,
                self.robot_frame,
                Time(),
            )
        except TransformException as exc:
            self.get_logger().warn(
                f'Waiting for {self.source_map_frame}->{self.robot_frame}: {exc}',
                throttle_duration_sec=5.0,
            )
            return

        src_trans = transform_msg.transform.translation
        src_rot = transform_msg.transform.rotation
        source_to_robot = (
            quaternion_to_matrix((src_rot.x, src_rot.y, src_rot.z, src_rot.w)),
            [src_trans.x, src_trans.y, src_trans.z],
        )

        yaw = yaw_from_quaternion((src_rot.x, src_rot.y, src_rot.z, src_rot.w))
        target_to_robot_flat = (
            yaw_matrix(yaw),
            [src_trans.x, src_trans.y, self.target_z],
        )

        target_to_source = compose(target_to_robot_flat, invert(source_to_robot))
        rot, trans = target_to_source
        qx, qy, qz, qw = matrix_to_quaternion(rot)

        projected_msg = TransformStamped()
        projected_msg.header.stamp = transform_msg.header.stamp
        projected_msg.header.frame_id = self.target_map_frame
        projected_msg.child_frame_id = self.source_map_frame
        projected_msg.transform.translation.x = trans[0]
        projected_msg.transform.translation.y = trans[1]
        projected_msg.transform.translation.z = trans[2]
        projected_msg.transform.rotation.x = qx
        projected_msg.transform.rotation.y = qy
        projected_msg.transform.rotation.z = qz
        projected_msg.transform.rotation.w = qw

        self.tf_broadcaster.sendTransform(projected_msg)


def main(args=None):
    rclpy.init(args=args)
    node = MapFrameProjector()
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
