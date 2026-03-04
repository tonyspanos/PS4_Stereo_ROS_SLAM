#!/usr/bin/env python3

import rospy
import rospkg
import cv2
import os
import yaml
import numpy as np
from cv_bridge import CvBridge
from sensor_msgs.msg import Image, CameraInfo

rospack = rospkg.RosPack()

def get_calibration_files(cam_number):
    """Get calibration file paths based on camera number.
    Both PS4 VR cameras share the same calibration since they are the same model.
    For per-camera calibration, place files in calibration/cam_<N>/{left,right}.yaml.
    """
    base_path = rospack.get_path('PSVR_cam_core') + '/calibration'

    cam_specific = os.path.join(base_path, f'cam_{cam_number}')
    if os.path.isdir(cam_specific):
        left_file = os.path.join(cam_specific, 'left.yaml')
        right_file = os.path.join(cam_specific, 'right.yaml')
    else:
        left_file = os.path.join(base_path, 'left.yaml')
        right_file = os.path.join(base_path, 'right.yaml')

    return left_file, right_file



def initialize(CAM_NUMBER):
    camera = cv2.VideoCapture(CAM_NUMBER)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 3448)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 808)

    return camera

def decode(frame):
    """Decode the PS4 VR camera's raw 3448x808 interleaved frame into left/right images.

    The sensor layout (per row, 3448 px wide):
      [64 px padding] [1264 px left] [48 px gap] [1264 px right] [808 px unused]
    Each image is 800 rows tall.  pyrDown halves to 632x400 for processing.
    """
    left = frame[0:800, 64:1328]       # cols 64..1327  (1264 wide)
    right = frame[0:800, 1328:2592]     # cols 1328..2591 (1264 wide)

    left = cv2.pyrDown(left)
    right = cv2.pyrDown(right)

    return (left, right)

def parse_yaml(filename):
    with open(filename, 'r') as stream:
        calib_data = yaml.safe_load(stream)
    cam_info = CameraInfo()
    cam_info.header.frame_id = "psvr"  # will be updated in main with namespace parameter
    cam_info.width = calib_data['image_width']
    cam_info.height = calib_data['image_height']
    cam_info.K = calib_data['camera_matrix']['data']
    cam_info.D = calib_data['distortion_coefficients']['data']
    cam_info.R = calib_data['rectification_matrix']['data']
    cam_info.P = calib_data['projection_matrix']['data']
    cam_info.distortion_model = calib_data['distortion_model']
    cam_info.binning_x = calib_data['binning_x']
    cam_info.binning_y = calib_data['binning_y']
    cam_info.roi.x_offset = calib_data['roi']['x_offset']
    cam_info.roi.y_offset = calib_data['roi']['y_offset']
    cam_info.roi.height = calib_data['roi']['height']
    cam_info.roi.width = calib_data['roi']['width']
    cam_info.roi.do_rectify = calib_data['roi']['do_rectify']

    return cam_info

if __name__ == "__main__":
    # setup the node that will be running
    rospy.init_node("psvr_core")

    # Get camera number from ROS parameter (default to 0)
    cam_number = rospy.get_param('~cam_number', 0)
    
    # Get camera namespace from ROS parameter (default to 'psvr')
    camera_namespace = rospy.get_param('~camera_namespace', 'psvr')
    
    rospy.loginfo(f"Starting PSVR camera publisher for camera {cam_number} in namespace '{camera_namespace}'")

    # Get calibration files for this camera
    left_file, right_file = get_calibration_files(cam_number)
    
    # setup the publisher where the images will be published
    raw_left = rospy.Publisher(f'{camera_namespace}/left/image_raw', Image, queue_size=10)
    raw_right = rospy.Publisher(f'{camera_namespace}/right/image_raw', Image, queue_size=10)

    # we also have to publish the info for each image
    info_left = rospy.Publisher(f'{camera_namespace}/left/camera_info', CameraInfo, queue_size=10)
    info_right = rospy.Publisher(f'{camera_namespace}/right/camera_info', CameraInfo, queue_size=10)

    # setup the camera
    psvr = initialize(cam_number)

    # setup cv2 to ros conversion
    bridge = CvBridge()

    # get camera info ready to be published
    left_cam_info = parse_yaml(left_file)
    right_cam_info = parse_yaml(right_file)


    rate = rospy.Rate(30)

    # run while ros is not shutdown
    while not rospy.is_shutdown():
        # gather the image
        ret, frame = psvr.read()
        if not ret or frame is None:
            rospy.logwarn("Failed to read frame from camera %d", cam_number)
            rate.sleep()
            continue

        # crop left and right
        left, right = decode(frame)

        # convert cv2 images to ROS
        leftImgMsg = bridge.cv2_to_imgmsg(left, "bgr8")
        rightImgMsg = bridge.cv2_to_imgmsg(right, "bgr8")

        # give the images being published a frame id. Used for RTAB-Map odometry
        leftImgMsg.header.frame_id = camera_namespace
        rightImgMsg.header.frame_id = camera_namespace

        # set time stamps for both the images and their camera info
        cap_time = rospy.Time.now()
        leftImgMsg.header.stamp = cap_time
        rightImgMsg.header.stamp = cap_time

        left_cam_info.header.stamp = cap_time
        right_cam_info.header.stamp = cap_time

        # publish image to topic
        raw_left.publish(leftImgMsg)
        raw_right.publish(rightImgMsg)

        # publish image info to topic
        info_left.publish(left_cam_info)
        info_right.publish(right_cam_info)

        rate.sleep()
