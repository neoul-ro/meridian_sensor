# meridian_sensor

Meridian 로봇의 센서 드라이버: Velodyne VLP-16 (라이다), RealSense D435 (카메라),
VectorNav VN-100 (IMU, 100Hz).

## 입출력

| 토픽 | 타입 | 방향 |
|---|---|---|
| /lidar/points | sensor_msgs/PointCloud2 (10Hz) | 발행 |
| /camera/rgb | sensor_msgs/Image (rgb8, 30Hz) | 발행 |
| /camera/depth | sensor_msgs/Image (32FC1, 미터 단위, 무효값 = NaN) | 발행 |
| /camera/info | sensor_msgs/CameraInfo | 발행 |
| /vectornav/imu | sensor_msgs/Imu (100Hz) | 발행 |
| /camera/camera/color/image_slam | sensor_msgs/Image (rgb8, 10Hz) | 발행 |

`/camera/rgb`, `/camera/depth`, `/camera/info` 는 프레임당 `header.stamp` 가 같다.
네이티브 드라이버 토픽(`/velodyne_points`, `/camera/camera/...`)도 그대로 나가고,
위 계약 토픽들은 그것의 zero-copy 릴레이다 (`/camera/depth` 만 `depth_image_proc`
로 16UC1 mm → 32FC1 m 변환).

`/camera/camera/color/image_slam` 은 성격이 다르다. 컬러 스트림을 30Hz → 10Hz 로
줄인 것으로, 매 프레임이 필요하지 않은 `meridian_slam` 의 VIO 전용이다.
**동기화가 아니라 프레임 예산이다** — `topic_tools throttle` 은 라이다 스윕을
전혀 모르는 단순 레이트 리미터이고, 실측 간격이 100~200ms 로 흔들린다. 대신
메시지를 손대지 않고 그대로 다시 내보내므로 `header.stamp` 이 원본 촬영 시각으로
남고, 시간 정렬은 SLAM 쪽이 `img_time_offset` 으로 한다. 이 토픽은 다른 데서
구독하지 않는다 — 인지 스택은 위의 30Hz 계약 토픽을 쓴다.

## 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| velodyne_ip | string | 192.168.1.201 | VLP-16 IP 주소 (lidar.launch.py) |
| enable_depth | bool | true | D435 깊이 + 컬러 정렬 깊이 (camera.launch.py) |
| vectornav_port | string | /dev/ttyUSB0 | VN-100 시리얼 포트 (imu.launch.py) |
| vectornav_baud | int | 921600 | VN-100 보드레이트. 115200 으로는 100Hz 가 안 나온다 (imu.launch.py) |
| imu_rate_divisor | int | 8 | 800Hz / divisor = IMU 주기. 8 → 100Hz, 4 → 200Hz (imu.launch.py) |

## 실행

```bash
ros2 launch meridian_sensor lidar.launch.py
ros2 launch meridian_sensor camera.launch.py
ros2 launch meridian_sensor imu.launch.py
```

의존: `ros-humble-velodyne`, `ros-humble-realsense2-camera`,
`ros-humble-topic-tools`, `ros-humble-depth-image-proc` (apt) — VectorNav
드라이버는 이 저장소에 포함돼 있다 (`vectornav/`).
