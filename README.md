# meridian_sensor

Meridian 로봇의 센서 드라이버. 라이다(VLP-16), 카메라(RealSense D435),
IMU(VectorNav VN-100)를 띄운다.

## 설치

```bash
sudo apt install \
    ros-humble-velodyne ros-humble-velodyne-pointcloud ros-humble-velodyne-driver \
    ros-humble-realsense2-camera \
    ros-humble-topic-tools \
    ros-humble-depth-image-proc
```

VectorNav 드라이버는 이 저장소에 들어 있어서 따로 받을 필요 없다.

## 빌드

```bash
cd ~/meridian_test_juyoung
colcon build --packages-select meridian_sensor vectornav vectornav_msgs
source install/setup.bash
```

## 실행

셋을 따로 띄운다. 각각 다른 터미널에서.

```bash
ros2 launch meridian_sensor lidar.launch.py     # 라이다
ros2 launch meridian_sensor camera.launch.py    # 카메라
ros2 launch meridian_sensor imu.launch.py       # IMU
```

잘 떴는지 확인:

```bash
ros2 topic hz /lidar/points      # 10 Hz
ros2 topic hz /camera/rgb        # 30 Hz
ros2 topic hz /vectornav/imu     # 100 Hz
```

값을 바꾸고 싶으면 명령줄에 붙인다.

```bash
ros2 launch meridian_sensor lidar.launch.py velodyne_ip:=192.168.1.99
ros2 launch meridian_sensor imu.launch.py vectornav_port:=/dev/ttyUSB1
```

받을 수 있는 인자 전체는 `--show-args` 로 본다.

```bash
ros2 launch meridian_sensor camera.launch.py --show-args
```

---

토픽·파라미터 목록과 설계 근거는 [docs/interface.md](docs/interface.md).
