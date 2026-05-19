# project_ros2

Cài đặt
1. Tạo workspace:
```
mkdir -p ~/ros2_ws
cd ros2_ws
```
2. Clone package:
```
git clone https://github.com/linhnghu/ros2
mv ros2 src
```
3. Cấp quyền thực thi cho file
```
chmod +x ~/ros2_ws/src/my_robot_urdf/scripts/teleop.py
chmod +x ~/ros2_ws/src/my_robot_urdf/scripts/arm_commander.py
```
4. Build package:
```
cd ~/ros2_ws
colcon build
```
5. Source môi trường:
```
source install/setup.bash
```
6. Chạy file launch
6.1. Chạy Slam_toolbox
```
ros2 launch my_robot_urdf launch_slam_toolbox.py
```
6.2. Chạy Cartographer 2D
```
ros2 launch my_robot_urdf launch_cato.py
```
6.3. Chạy Lio-sam
```
ros2 launch my_robot_urdf launch.py
```
