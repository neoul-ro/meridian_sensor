# meridian_sensor

Sensor drivers for the Meridian robot: Velodyne VLP-16 (LiDAR), RealSense D435 (camera), VectorNav VN-100 (IMU, 100Hz).

## I/O

| Topic | Type | Direction |
|---|---|---|
| /lidar/points | sensor_msgs/PointCloud2 (10Hz) | publish |
| /camera/rgb | sensor_msgs/Image (rgb8, 30Hz) | publish |
| /camera/depth | sensor_msgs/Image (32FC1, meters; invalid = NaN) | publish |
| /camera/info | sensor_msgs/CameraInfo | publish |
| /vectornav/imu | sensor_msgs/Imu (100Hz) | publish |

`/camera/rgb`, `/camera/depth`, `/camera/info` share the same `header.stamp` per frame.
Native driver topics (`/velodyne_points`, `/camera/camera/...`) are also published unchanged;
the schema topics above are zero-copy relays (`/camera/depth` is converted 16UC1 mm -> 32FC1 m
by `depth_image_proc`).

## Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| velodyne_ip | string | 192.168.1.201 | VLP-16 IP address (lidar.launch.py) |
| enable_depth | bool | true | D435 depth + color-aligned depth (camera.launch.py) |
| vectornav_port | string | /dev/ttyUSB0 | VN-100 serial port (imu.launch.py) |
| vectornav_baud | int | 921600 | VN-100 baud; 115200 cannot carry 100Hz (imu.launch.py) |
| imu_rate_divisor | int | 8 | 800Hz / divisor = IMU rate; 8 -> 100Hz, 4 -> 200Hz (imu.launch.py) |

## Run

```bash
ros2 launch meridian_sensor lidar.launch.py
ros2 launch meridian_sensor camera.launch.py
ros2 launch meridian_sensor imu.launch.py
```

Dependencies: `ros-humble-velodyne`, `ros-humble-realsense2-camera`, `ros-humble-topic-tools`,
`ros-humble-depth-image-proc` (apt) — the VectorNav driver is included in this repo (`vectornav/`).
