import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import (
    DeclareLaunchArgument, IncludeLaunchDescription, SetEnvironmentVariable,
    TimerAction
)
from launch.conditions import IfCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import EnvironmentVariable, LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    use_lio_sam = LaunchConfiguration('use_lio_sam')
    use_cartographer = LaunchConfiguration('use_cartographer')
    use_slam_toolbox = LaunchConfiguration('use_slam_toolbox') # <-- THÊM ĐÂY
    use_rviz = LaunchConfiguration('rviz')
    use_teleop = LaunchConfiguration('teleop')
    use_arm_commander = LaunchConfiguration('arm_commander')
    gazebo_gui = LaunchConfiguration('gazebo_gui')

    # ── Paths ──────────────────────────────────────────────────────────────
    package_name = 'my_robot_urdf'
    pkg_share    = get_package_share_directory(package_name)
    urdf_file    = os.path.join(pkg_share, 'urdf', 'rv2_2d_slam_toolbox.urdf')
    rviz_config_file = os.path.join(pkg_share, 'my_robot_urdf', 'slam_toolbox.rviz')

    with open(urdf_file, 'r') as f:
        robot_desc = f.read()
    robot_desc = robot_desc.replace('$(find my_robot_urdf)', pkg_share)

    # ── 1. GAZEBO_MODEL_PATH ───────────────────────────────────────────────
    pkg_parent = os.path.abspath(os.path.join(pkg_share, '..'))
    set_gazebo_model_path = SetEnvironmentVariable(
        name='GAZEBO_MODEL_PATH', value=pkg_parent
    )
    set_gazebo_plugin_path = SetEnvironmentVariable(
        name='GAZEBO_PLUGIN_PATH',
        value=[
            os.path.join(os.path.abspath(os.path.join(pkg_share, '..', '..', '..')), 'velodyne_gazebo_plugins', 'lib'),
            ':',
            '/home/linh/lio_sam_gazebo_ros2/build/velodyne_gazebo_plugins:',
            EnvironmentVariable('GAZEBO_PLUGIN_PATH', default_value='')
        ]
    )

    # ── 2. Robot State Publisher ───────────────────────────────────────────
    robot_state_publisher = Node(
        package='robot_state_publisher',
        executable='robot_state_publisher',
        output='screen',
        parameters=[{'robot_description': robot_desc, 'use_sim_time': True}]
    )

    # ── 3. Gazebo — dùng world có vật cản
    world_path = os.path.join(pkg_share, 'worlds', 'cartographer_test.world')

    gazebo_launch_file = os.path.join(
        get_package_share_directory('gazebo_ros'), 'launch', 'gazebo.launch.py'
    )
    gazebo = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(gazebo_launch_file),
        launch_arguments={
            'world':   world_path,
            'verbose': 'false',    
            'gui': gazebo_gui,
            'extra_gazebo_args': '--ros-args -p use_sim_time:=true',
        }.items()
    )

    # ── 4. Spawn Robot ─────────────────────────────────────────────────────
    spawn_robot = Node(
        package='gazebo_ros',
        executable='spawn_entity.py',
        arguments=['-entity', 'robot_rv2', '-topic', 'robot_description'],
        output='screen'
    )

    # ── 5. Controllers ─────────────────────────────────────────────────────
    load_joint_state_broadcaster = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['joint_state_broadcaster'],
        output='screen',
    )
    load_arm_controller = Node(
        package='controller_manager',
        executable='spawner',
        arguments=['arm_controller'],
        output='screen',
    )

    # ── 6. Teleop & Arm commander ──────────────────────────────────────────
    arm_commander_node = Node(
        package='my_robot_urdf',
        executable='arm_commander.py',
        name='arm_commander',
        output='screen',
        parameters=[{'use_sim_time': True}],
        prefix=['gnome-terminal -- '],
        condition=IfCondition(use_arm_commander)
    )
    teleop_node = Node(
        package='my_robot_urdf',
        executable='teleop.py',
        name='teleop',
        output='screen',
        parameters=[{'use_sim_time': True}],
        prefix=['gnome-terminal -- '],
        condition=IfCondition(use_teleop)
    )

    # ── 7. Stabilized IMU + Cartographer 3D ────────────────────────────────
    imu_stabilizer_node = Node(
        package='my_robot_urdf',
        executable='imu_stabilizer.py',
        name='imu_stabilizer',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'input_topic': '/imu/data'},
            {'output_topic': '/imu/cartographer'},
            {'frame_id': 'base_link'},
            {'gravity': 9.80665},
        ],
    )
    lio_sam_imu_stabilizer_node = Node(
        package='my_robot_urdf',
        executable='imu_stabilizer.py',
        name='lio_sam_imu_stabilizer',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'input_topic': '/imu/data'},
            {'output_topic': '/imu/lio_sam'},
            {'frame_id': 'imu_link'},
            {'gravity': 9.80665},
        ],
    )

    map_frame_projector_node = Node(
        package='my_robot_urdf',
        executable='map_frame_projector.py',
        name='map_frame_projector',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'target_map_frame': 'map'},
            {'source_map_frame': 'cartographer_map'},
            {'robot_frame': 'base_footprint'},
            {'publish_period_sec': 0.02},
            {'target_z': 0.0},
        ],
    )

    cartographer_node = Node(
        package='cartographer_ros',
        executable='cartographer_node',
        name='cartographer_node',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=[
            '-configuration_directory', os.path.join(pkg_share, 'config'),
            '-configuration_basename', 'cartographer_2d.lua',
        ],
        remappings=[
                ('/lidar_plugin', '/scan'), 
                ('/imu', '/imu/data')             
            ],
    )

    cartographer_occupancy_grid_node = Node(
        package='cartographer_ros',
        executable='cartographer_occupancy_grid_node',
        name='occupancy_grid_node',
        output='screen',
        parameters=[
            {'use_sim_time': True},
            {'resolution': 0.05},
            {'publish_period_sec': 1.0},
        ],
    )

    # ── 7.5. SLAM TOOLBOX (MỚI THÊM) ────────────────────────────────────────
    # Khai báo file launch gốc từ gói slam_toolbox quốc dân
    slam_toolbox_launch_file = os.path.join(
        get_package_share_directory('slam_toolbox'), 'launch', 'online_async_launch.py'
    )
    
    # Include file launch đó vào đây kèm tham số map_frame, odom_frame nếu cần thiết
    # Mặc định slam_toolbox sẽ đọc scan từ topic `/scan`.
    slam_toolbox = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(slam_toolbox_launch_file),
        launch_arguments={
            'use_sim_time': 'true',
            # Nếu robot của bạn đẩy topic khác ví dụ /lidar_plugin, 
            # hãy sửa file config của slam_toolbox hoặc bổ sung remapping.
        }.items(),
        condition=IfCondition(use_slam_toolbox)
    )

    # ── 8. RViz ────────────────────────────────────────────────────────────
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        output='screen',
        parameters=[{'use_sim_time': True}],
        arguments=['-d', rviz_config_file],
    )

    # ── 9. Delay cho Cartographer ─────────────────────────────────────────
    delayed_cartographer = TimerAction(
        period=3.0,
        actions=[
            cartographer_node,
            map_frame_projector_node,
            cartographer_occupancy_grid_node,
        ],
        condition=IfCondition(use_cartographer)
    )

    # ── 9.5. Delay cho SLAM Toolbox (MỚI THÊM) ────────────────────────────
    # Chờ 3 giây giống Cartographer để Gazebo ổn định TF phát ra từ robot
    delayed_slam_toolbox = TimerAction(
        period=3.0,
        actions=[slam_toolbox],
        condition=IfCondition(use_slam_toolbox)
    )

    delayed_rviz = TimerAction(
        period=10.0,
        actions=[rviz_node]
    )

    # ── 10. LIO-SAM ───────────────────────────────────────────────────────
    lio_sam_launch_file = os.path.join(
        get_package_share_directory('lio_sam'), 'launch', 'run.launch.py'
    )
    lio_sam_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(lio_sam_launch_file),
        launch_arguments={
            'params_file': os.path.join(
                get_package_share_directory('lio_sam'), 'config', 'params.yaml'
            ),
            'rviz': use_rviz,
            'publish_map_odom_tf': 'false',
            'use_imu_preintegration': 'false',
        }.items(),
        condition=IfCondition(use_lio_sam)
    )
    lio_sam_imu_stabilizer_node_target = TimerAction(
        period=4.0,
        actions=[lio_sam_imu_stabilizer_node],
        condition=IfCondition(use_lio_sam)
    )
    delayed_lio_sam = TimerAction(
        period=12.0,
        actions=[lio_sam_launch],
        condition=IfCondition(use_lio_sam)
    )

    # ── Return ─────────────────────────────────────────────────────────────
    return LaunchDescription([
        # Khai báo các tham số điều khiển bật/tắt thuật toán SLAM
        DeclareLaunchArgument('use_lio_sam', default_value='false'),
        DeclareLaunchArgument('use_cartographer', default_value='false'), # Mặc định tắt Cartographer đi
        DeclareLaunchArgument('use_slam_toolbox', default_value='true'),  # Mặc định BẬT SLAM Toolbox
        DeclareLaunchArgument('rviz', default_value='true'),
        DeclareLaunchArgument('teleop', default_value='true'),
        DeclareLaunchArgument('arm_commander', default_value='true'),
        DeclareLaunchArgument('gazebo_gui', default_value='true'),
        
        set_gazebo_model_path,
        set_gazebo_plugin_path,
        robot_state_publisher,
        gazebo,
        spawn_robot,
        load_joint_state_broadcaster,
        load_arm_controller,
        arm_commander_node,
        teleop_node,
        
        # Các khối SLAM chạy theo điều kiện đóng/mở ngắt quãng
        delayed_cartographer,
        delayed_slam_toolbox, # <-- THÊM VÀO ĐÂY
        #delayed_lio_sam_imu,
        #delayed_lio_sam,
        delayed_rviz,
    ])
