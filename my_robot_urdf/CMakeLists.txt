cmake_minimum_required(VERSION 3.8)
project(my_robot_urdf)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

# 1. Cài đặt các thư mục dữ liệu (Đưa vào mục share)
# Đã thêm thư mục 'rviz' vào danh sách này
install(
  DIRECTORY launch meshes urdf scripts config my_robot_urdf worlds
  DESTINATION share/${PROJECT_NAME}
)

# 2. Cài đặt các file thực thi (Đưa vào mục lib)
# Chỉ để lại file teleop.py ở đây thôi
install(PROGRAMS
  scripts/teleop.py scripts/arm_commander.py scripts/imu_stabilizer.py scripts/map_frame_projector.py
  DESTINATION lib/${PROJECT_NAME}
)

ament_package()
