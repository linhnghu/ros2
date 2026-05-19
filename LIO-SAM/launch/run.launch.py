import os
from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

def generate_launch_description():

    share_dir = get_package_share_directory('lio_sam')
    parameter_file = LaunchConfiguration('params_file')
    rviz = LaunchConfiguration('rviz')
    publish_map_odom_tf = LaunchConfiguration('publish_map_odom_tf')
    use_imu_preintegration = LaunchConfiguration('use_imu_preintegration')
    
    # xacro_path = os.path.join(share_dir, 'config', 'robot.urdf.xacro')
    rviz_config_file = os.path.join(share_dir, 'config', 'rviz2.rviz')

    params_declare = DeclareLaunchArgument(
        'params_file',
        default_value=os.path.join(
            share_dir, 'config', 'params.yaml'),
        description='Path to the ROS2 parameters file to use.')
    rviz_declare = DeclareLaunchArgument(
        'rviz',
        default_value='true',
        description='Start RViz with the LIO-SAM config.')
    publish_map_odom_tf_declare = DeclareLaunchArgument(
        'publish_map_odom_tf',
        default_value='false',
        description='Publish a static map->odom transform for standalone visualization.')
    use_imu_preintegration_declare = DeclareLaunchArgument(
        'use_imu_preintegration',
        default_value='true',
        description='Start LIO-SAM IMU preintegration. Disable for Gazebo planar robots that use scan matching only.')

    return LaunchDescription([
        params_declare,
        rviz_declare,
        publish_map_odom_tf_declare,
        use_imu_preintegration_declare,

        Node(
            package='tf2_ros',
            executable='static_transform_publisher',
            arguments='0.0 0.0 0.0 0.0 0.0 0.0 map odom'.split(' '),
            parameters=[parameter_file],
            condition=IfCondition(publish_map_odom_tf),
            output='screen'
        ),

        Node(
            package='lio_sam',
            executable='lio_sam_imuPreintegration',
            name='lio_sam_imuPreintegration',
            parameters=[parameter_file],
            condition=IfCondition(use_imu_preintegration),
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_imageProjection',
            name='lio_sam_imageProjection',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_featureExtraction',
            name='lio_sam_featureExtraction',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='lio_sam',
            executable='lio_sam_mapOptimization',
            name='lio_sam_mapOptimization',
            parameters=[parameter_file],
            output='screen'
        ),
        Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config_file],
            condition=IfCondition(rviz),
            output='screen'
        )
    ])
