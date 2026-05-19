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
chmod +x ~/ros2_ws/src/my_robot_urdf/scripts/imu_stabilizer.py
chmod +x ~/ros2_ws/src/my_robot_urdf/scripts/map_frame_projector.py
```
4. Các gói cần thiết
```
sudo apt update
sudo apt install ros-humble-slam-toolbox
sudo apt install ros-humble-cartographer ros-humble-cartographer-ros
sudo apt install -y libgtsam-dev libgtsam-unstable-dev
sudo apt install -y ros-humble-perception-pcl ros-humble-pcl-msgs ros-humble-vision-opencv ros-humble-xacro
sudo apt install ros-humble-rviz2 ros-humble-tf2-ros ros-humble-robot-state-publisher ros-humble-nav2-bringup
sudo apt install ros-humble-ros2-control ros-humble-ros2-controllers
sudo apt install ros-humble-gazebo-ros2-control
```
5.Cài GTSAM
5.1. Cài dependency
```
sudo apt update
sudo apt install -y \
build-essential \
cmake \
libboost-all-dev \
libtbb-dev \
libeigen3-dev \
git
```
5.2. Clone GTSAM
```
cd ~
git clone https://github.com/borglab/gtsam.git
```
5.3. Build và install
```
cd ~/gtsam
mkdir build
cd build

cmake ..
make -j$(nproc)
sudo make install
```
5.4. 
```
sudo ldconfig
sed -i 's/boost::shared_ptr<gtsam::PreintegrationParams>/std::shared_ptr<gtsam::PreintegrationParams>/g' ~/ros2_ws/src/LIO-SAM/src/imuPreintegration.cpp
```
6. Build package:
```
cd ~/ros2_ws
colcon build
```
7. Source môi trường:
```
source install/setup.bash
```
8. Chạy file launch
8.1. Chạy Slam_toolbox
```
ros2 launch my_robot_urdf launch_slam_toolbox.py
```
8.2. Chạy Cartographer 2D
```
ros2 launch my_robot_urdf launch_cato.py
```
8.3. Chạy Lio-sam
```
ros2 launch my_robot_urdf launch.py
```
