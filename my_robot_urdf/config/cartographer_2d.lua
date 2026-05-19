include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "cartographer_map",
  
  -- Sửa thành imu_link vì Cartographer yêu cầu tracking_frame phải là frame của IMU 
  -- nếu bạn bật use_imu_data = true
  tracking_frame = "imu_link",
  
  -- Nên đặt published_frame là odom và để Cartographer KHÔNG tạo odom frame.
  -- Vì trong URDF, Gazebo Planar Move Plugin đã đảm nhận việc phát tf: odom -> base_footprint rồi.
  -- Cartographer chỉ cần phát tf: map -> odom là tạo thành một cây TF hoàn hảo.
  published_frame = "odom",
  odom_frame = "odom",
  provide_odom_frame = false, 
  
  publish_frame_projected_to_2d = true,
  use_pose_extrapolator = true,
  
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,

  num_laser_scans = 1,
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 0,

  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
  
  -- [QUAN TRỌNG] Hai biến bắt buộc phải có trong ROS 2 để không bị crash exit code -6
  publish_to_tf = true,
  publish_tracked_pose = false,
}

MAP_BUILDER.use_trajectory_builder_2d = true

TRAJECTORY_BUILDER_2D.use_imu_data = true 
TRAJECTORY_BUILDER_2D.min_range = 0.2
TRAJECTORY_BUILDER_2D.max_range = 20.0
TRAJECTORY_BUILDER_2D.missing_data_ray_length = 5.0
TRAJECTORY_BUILDER_2D.use_online_correlative_scan_matching = true

POSE_GRAPH.optimize_every_n_nodes = 35

return options
