#!/usr/bin/env python3

import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from builtin_interfaces.msg import Duration
import threading

class ArmCommander(Node):
    def __init__(self):
        super().__init__('arm_commander_node')
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/arm_controller/joint_trajectory', 
            10
        )
        self.get_logger().info("Chế độ nhập tay đã sẵn sàng!")

    def send_target_angles(self, angle1, angle2):
        msg = JointTrajectory()
        # Cập nhật thời gian chính xác vì rclpy.spin() đang chạy ngầm
        msg.header.stamp = self.get_clock().now().to_msg()
        msg.joint_names = ['arm1_joint', 'arm2_joint']
        
        point = JointTrajectoryPoint()
        point.positions = [float(angle1), float(angle2)]
        
        # BÁO CHO TAY MÁY DỪNG HẲN KHI ĐẾN NƠI (Vận tốc = 0)
        point.velocities = [0.0, 0.0] 
        
        # Cài đặt thời gian để tay máy đi đến vị trí đích (2 giây)
        point.time_from_start = Duration(sec=2, nanosec=0)
        
        msg.points = [point]
        self.publisher_.publish(msg)
        self.get_logger().info(f"Đã gửi lệnh: arm1={angle1} rad, arm2={angle2} rad")


def user_input_thread(node):
    """Luồng riêng biệt chỉ để xử lý việc nhập dữ liệu từ bàn phím"""
    while rclpy.ok():
        print("\n" + "="*40)
        print("ĐIỀU KHIỂN GÓC QUAY (Đơn vị: Radian)")
        print("Nhấn 'q' và Enter để thoát chương trình.")
        
        try:
            val1_str = input("Nhập góc quay cho arm1_joint: ")
            if val1_str.lower() == 'q':
                rclpy.shutdown() # Tắt ROS 2 nếu bấm q
                break
                
            val2_str = input("Nhập góc quay cho arm2_joint: ")
            if val2_str.lower() == 'q':
                rclpy.shutdown()
                break
                
            val1 = float(val1_str)
            val2 = float(val2_str)
            
            # Gửi lệnh
            node.send_target_angles(val1, val2)
            
        except ValueError:
            print("LỖI: Bạn phải nhập một số hợp lệ (ví dụ: 1.5, -0.7, 0)!")
        except EOFError:
            break

def main(args=None):
    rclpy.init(args=args)
    node = ArmCommander()
    
    # 1. Khởi tạo và chạy luồng nhập bàn phím
    input_thread = threading.Thread(target=user_input_thread, args=(node,))
    input_thread.start()
    
    try:
        # 2. Luồng chính sẽ liên tục spin để cập nhật thời gian từ Gazebo
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Đã dừng node.")
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()
        input_thread.join()

if __name__ == '__main__':
    main()
