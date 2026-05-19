include "map_builder.lua"
include "trajectory_builder.lua"

options = {
  map_builder = MAP_BUILDER,
  trajectory_builder = TRAJECTORY_BUILDER,
  map_frame = "cartographer_map",
  tracking_frame = "imu_link",
  published_frame = "base_footprint",
  odom_frame = "odom",
  provide_odom_frame = false,
  publish_frame_projected_to_2d = false,
  use_pose_extrapolator = true,
  use_odometry = true,
  use_nav_sat = false,
  use_landmarks = false,
  
  -- Sensor Inputs
  num_laser_scans = 0,                   -- Disable 2D scans
  num_multi_echo_laser_scans = 0,
  num_subdivisions_per_laser_scan = 1,
  num_point_clouds = 1,                  -- Enable 1 PointCloud2 topic
  
  -- Timing & Publishing
  lookup_transform_timeout_sec = 0.2,
  submap_publish_period_sec = 0.3,
  pose_publish_period_sec = 5e-3,
  trajectory_publish_period_sec = 30e-3,
  rangefinder_sampling_ratio = 1.,
  odometry_sampling_ratio = 1.,
  fixed_frame_pose_sampling_ratio = 1.,
  imu_sampling_ratio = 1.,
  landmarks_sampling_ratio = 1.,
}

-- Enable 3D SLAM
MAP_BUILDER.use_trajectory_builder_3d = true
MAP_BUILDER.num_background_threads = 4 -- Adjust based on your available CPU cores

-- Optimize based on your 3D LiDAR
-- If your LiDAR publishes full 360-degree sweeps in a single message (e.g., Ouster/Velodyne), keep this at 1.
TRAJECTORY_BUILDER_3D.num_accumulated_range_data = 1
TRAJECTORY_BUILDER_3D.imu_gravity_time_constant = 100.

POSE_GRAPH.constraint_builder.ceres_scan_matcher_3d.only_optimize_yaw = true
TRAJECTORY_BUILDER_3D.ceres_scan_matcher.only_optimize_yaw = false
POSE_GRAPH.optimization_problem.fix_z_in_3d = false

-- Giảm kích thước voxel để bản đồ chi tiết hơn
TRAJECTORY_BUILDER_3D.voxel_filter_size = 0.05
POSE_GRAPH.optimization_problem.use_online_imu_extrinsics_in_3d = false

return options
