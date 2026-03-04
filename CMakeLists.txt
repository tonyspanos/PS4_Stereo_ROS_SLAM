cmake_minimum_required(VERSION 3.0.2)
project(PSVR_cam_core)

find_package(catkin REQUIRED COMPONENTS
  rospy
  std_msgs
  sensor_msgs
  cv_bridge
  camera_info_manager
  image_transport
)

catkin_package(
  CATKIN_DEPENDS rospy std_msgs sensor_msgs cv_bridge camera_info_manager image_transport
)

include_directories(${catkin_INCLUDE_DIRS})

# Install Python nodes
catkin_install_python(PROGRAMS
  src/psvr_cam_publisher.py
  Firmware_loader/ps4eye_init.py
  DESTINATION ${CATKIN_PACKAGE_BIN_DESTINATION}
)

# Install launch files and calibration data
install(DIRECTORY launch/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/launch
)
install(DIRECTORY calibration/
  DESTINATION ${CATKIN_PACKAGE_SHARE_DESTINATION}/calibration
)
