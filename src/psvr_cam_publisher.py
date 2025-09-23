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
    """Get calibration file paths based on camera number"""
    base_path = rospack.get_path('PSVR_cam_core') + '/calibration'
    
    # For multi-camera setup, you might want different calibration files
    # For now, using the same calibration files for all cameras
    left_file = base_path + '/left.yaml'
    right_file = base_path + '/right.yaml'
    
    return left_file, right_file



def initialize(CAM_NUMBER):
    camera = cv2.VideoCapture(CAM_NUMBER)
    camera.set(cv2.CAP_PROP_FRAME_WIDTH, 3448)
    camera.set(cv2.CAP_PROP_FRAME_HEIGHT, 808)

    return camera

def decode(frame):
    left = np.zeros((800, 1264, 3), np.uint8)
    right = np.zeros((800, 1264, 3), np.uint8)

    for i in range(800):
        left[i] = frame[i, 64: 1280 + 48]
        right[i] = frame[i, 1280 + 48: 1280 + 48 + 1264]

    left = cv2.pyrDown(left)
    right = cv2.pyrDown(right)

    return (left, right)

def parse_yaml(filename):
    stream = open(filename, 'r')
    calib_data = yaml.load(stream)
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


    # run while ros is not shutdown
    while not rospy.is_shutdown():
        # gather the image
        ret, frame = psvr.read()

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
