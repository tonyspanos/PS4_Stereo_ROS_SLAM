FROM ros:noetic

# Noninteractive apt
ENV DEBIAN_FRONTEND=noninteractive

# Install system dependencies and ROS packages
RUN apt-get update && apt-get install -y \
  python3 \
  python3-pip \
  build-essential \
  cmake \
  git \
  wget \
  # Core ROS packages
  ros-noetic-catkin \
  python3-catkin-tools \
  ros-noetic-cv-bridge \
  ros-noetic-image-transport \
  ros-noetic-camera-info-manager \
  # RTAB-Map and SLAM dependencies
  ros-noetic-rtabmap-ros \
  ros-noetic-rtabmap \
  # Stereo processing
  ros-noetic-stereo-image-proc \
  ros-noetic-image-proc \
  # Transform and visualization
  ros-noetic-tf \
  ros-noetic-tf2-ros \
  ros-noetic-rviz \
  # Parameter configuration
  ros-noetic-rqt-reconfigure \
  ros-noetic-rqt-common-plugins \
  # OpenCV and camera support
  ros-noetic-usb-cam \
  libopencv-dev \
  python3-opencv \
  # USB and camera hardware support
  libusb-1.0-0-dev \
  udev \
  v4l-utils \
  && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
RUN python3 -m pip install \
  pyusb \
  pyyaml \
  numpy

# Setup workspace
WORKDIR /catkin_ws
RUN mkdir -p src

# Copy the package
COPY . /catkin_ws/src/PSVR_cam_core

# Build the workspace
RUN . /opt/ros/noetic/setup.sh && \
  catkin_make

# Add source command to bashrc
RUN echo "source /catkin_ws/devel/setup.bash" >> /root/.bashrc

# Make Python scripts executable
RUN chmod +x /catkin_ws/src/PSVR_cam_core/src/psvr_cam_publisher.py \
  && chmod +x /catkin_ws/src/PSVR_cam_core/Firmware_loader/ps4eye_init.py

# USB device access permissions
RUN echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="05a9", ATTRS{idProduct}=="0580", MODE="0666"' > /etc/udev/rules.d/99-ps4eye.rules \
  && echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="05a9", ATTRS{idProduct}=="058a", MODE="0666"' >> /etc/udev/rules.d/99-ps4eye.rules \
  && echo 'SUBSYSTEM=="usb", ATTRS{idVendor}=="05a9", ATTRS{idProduct}=="058b", MODE="0666"' >> /etc/udev/rules.d/99-ps4eye.rules

# Set environment variables for display
ENV DISPLAY=:0
ENV QT_X11_NO_MITSHM=1

ENTRYPOINT ["/ros_entrypoint.sh"]
CMD ["bash"]