# PS4_Stereo_ROS_SLAM

A ROS Noetic node for dual PS4 VR USB cameras performing stereo SLAM with RTAB-Map. Two cameras are mounted ~3 cm apart on a pole — one facing forward, one facing backward — providing 360° stereo coverage for under $50.

## Purpose

This project served as a refresher for ROS Noetic and to give me the opportunity to educate myself about the `stereo_image_proc` and `rtab-map` ROS nodes. The code and results from this project will be rolled into further thesis work. I will be applying similar SLAM techniques to autonomous navigation in offroad 'hiking trail' environments in the near future. To my knowledge this is the first implementation of RTAB-Map using the PlayStation 4 VR camera (definitely first in ROS Noetic).

## Requirements

1.  Ubuntu 20.04
2.  ROS Noetic
3.  **Two** PS4 VR cameras (modified to connect through USB 3.0)
4.  Camset ([git repo](https://github.com/azeam/camset))
5.  camera_calibration ROS package ([ROS page](http://wiki.ros.org/camera_calibration))
6.  rtabmap_ros ROS package ([ROS page](http://wiki.ros.org/rtabmap_ros))

## Hardware Setup

Both cameras must be flashed with the PS4 eye firmware before use. The cameras are mounted on a pole approximately 3 cm apart (same Y and Z position). Camera 0 faces forward and camera 1 faces backward, giving full front-and-back stereo coverage.

## Setup

1.  Fork this repository and install all requirements. This assumes you already have a ROS environment set up and have an intermediate understanding of how ROS functions.
2.  Flash the USB firmware on **both** PS4 cameras using the Python script found in the _Firmware_loader_ folder: `sudo python3 Firmware_loader/ps4eye_init.py`. The script will detect and flash all connected uninitialized cameras automatically.
3.  Run camset (`camset`) and note the input device numbers for both PS4 cameras. Set each camera's exposure to _shutter priority_ instead of _automatic_.
4.  Complete camera calibration for both cameras (see Calibration section below).
5.  Launch the system:
    ```bash
    roslaunch PSVR_cam_core psvr_launch.launch cam0_device:=0 cam1_device:=1
    ```
    Adjust `cam0_device` and `cam1_device` to match the device numbers from step 3.

### Launch Arguments

| Argument          | Default | Description                                |
| ----------------- | ------- | ------------------------------------------ |
| `delete_db`       | `true`  | Delete the RTAB-Map database on start      |
| `camera_baseline` | `0.03`  | Distance between the two cameras (metres)  |
| `cam0_device`     | `0`     | `/dev/video` index for the forward camera  |
| `cam1_device`     | `1`     | `/dev/video` index for the backward camera |

## Docker

A Docker setup is provided for reproducible builds:

```bash
docker build -t ps4-slam .
docker-compose up
```

The `docker-compose.yaml` maps the X11 display and USB devices into the container.

## Node Map

If set up correctly the node map should look like the following.

## Calibration

The following steps should be taken to calibrate your PS4 cameras. The repository comes with calibration files but more accurate results can be achieved after calibration.

1.  Download, print, and build a calibration board.
2.  Run the camera_calibration ROS package and follow their calibration tutorial.
3.  Instead of committing the calibration parameters to the camera, save them to a file (the file will be saved to the `tmp/` folder).
4.  Copy and paste the left and right camera calibration parameters to their respective `.yaml` files found in the `calibration/` folder.
5.  For per-camera calibration, create `calibration/cam_0/` and `calibration/cam_1/` directories with their own `left.yaml` and `right.yaml`. If these directories don't exist, both cameras share the default calibration files.

## Example Results

Examples have been processed using CloudCompare.

## Extras

A few extras have been included in this package.

1.  A small 8.5"×11" calibration board (each square is approximately 22 mm at 100% size).
2.  A debug launch file (`psvr_launch_static_image.launch`) that runs a single camera with `stereo_image_proc` for tuning in RViz.
