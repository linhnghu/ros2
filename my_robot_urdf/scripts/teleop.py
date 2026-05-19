#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
import sys
import tty
import termios

class CustomTeleop(Node):
    def __init__(self):
        super().__init__('custom_teleop')
        self.pub = self.create_publisher(Twist, '/cmd_vel', 10)
        
        # ---- Tinh chỉnh ở đây ----
        self.linear_speed  = 0.5   # m/s
        self.angular_speed = 3.0   # rad/s
        # --------------------------
        
        print("""
        Điều khiển robot:
        -----------------
        i : Tiến thẳng
        , : Lùi
        u : Quay trái tại chỗ
        o : Quay phải tại chỗ
        j : Tiến + quay trái
        l : Tiến + quay phải
        J : Đi ngang sang trái
        L : Đi ngang sang phải
        k : Dừng
        q : Thoát
        """)

    def get_key(self):
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            key = sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
        return key

    def stop_robot(self):
        """Gửi lệnh vận tốc 0 để dừng robot an toàn."""
        msg = Twist()
        msg.linear.x = 0.0
        msg.linear.y = 0.0
        msg.angular.z = 0.0
        self.pub.publish(msg)

    def run(self):
        while True:
            key = self.get_key()
            msg = Twist()

            if key == 'i':                         # Tiến thẳng
                msg.linear.x  = self.linear_speed
                msg.angular.z = 0.0

            elif key == ',':                       # Lùi
                msg.linear.x  = -self.linear_speed
                msg.angular.z = 0.0

            elif key == 'u':                       # Quay trái tại chỗ
                msg.linear.x  = 0.0
                msg.angular.z = self.angular_speed

            elif key == 'o':                       # Quay phải tại chỗ
                msg.linear.x  = 0.0
                msg.angular.z = -self.angular_speed

            elif key == 'j':                       # Tiến + quay trái
                msg.linear.x  = self.linear_speed
                msg.angular.z = self.angular_speed

            elif key == 'l':                       # Tiến + quay phải
                msg.linear.x  = self.linear_speed
                msg.angular.z = -self.angular_speed

            elif key == 'k':                       # Dừng
                msg.linear.x  = 0.0
                msg.angular.z = 0.0
                
            elif key == 'J':                       # Đi ngang sang trái
                msg.linear.y  = self.linear_speed
                msg.angular.z = 0.0

            elif key == 'L':                       # Đi ngang sang phải
                msg.linear.y  = -self.linear_speed
                msg.angular.z = 0.0
                
            elif key == 'q':                       # Thoát
                self.stop_robot()
                break
            
            # Gửi lệnh điều khiển nếu không nhấn thoát
            if key != 'q':
                self.pub.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = CustomTeleop()
    
    try:
        node.run()
    except KeyboardInterrupt:
        # Bắt sự kiện khi người dùng nhấn Ctrl+C
        node.stop_robot()
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
