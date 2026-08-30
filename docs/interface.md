# meridian_sensor 인터페이스

발행 토픽, 파라미터, 그리고 왜 그렇게 만들었는지. 실행 방법은 저장소 루트의
`README.md` 를 본다.

## 발행 토픽

| 토픽 | 타입 | 비고 |
|---|---|---|
| `/lidar/points` | `sensor_msgs/PointCloud2` | 10Hz |
| `/camera/rgb` | `sensor_msgs/Image` | rgb8, 30Hz |
| `/camera/depth` | `sensor_msgs/Image` | 32FC1, 미터 단위, 무효값 = NaN |
| `/camera/info` | `sensor_msgs/CameraInfo` | 30Hz |
| `/vectornav/imu` | `sensor_msgs/Imu` | 100Hz |
| `/camera/camera/color/image_slam` | `sensor_msgs/Image` | rgb8, 10Hz. SLAM 전용 |

`/camera/rgb`, `/camera/depth`, `/camera/info` 는 프레임당 `header.stamp` 가
같다. 하류(geobuilder)가 세 토픽을 한 프레임으로 묶는 근거라 **바꾸면 안 된다.**

네이티브 드라이버 토픽(`/velodyne_points`, `/camera/camera/...`)도 그대로 나간다.
위 계약 토픽들은 그것의 zero-copy 릴레이다. `/camera/depth` 만 예외로
`depth_image_proc` 이 16UC1 mm → 32FC1 m 로 변환한다.

## image_slam — 왜 10Hz 인가

컬러 스트림을 30Hz → 10Hz 로 줄여서 `meridian_slam` 의 VIO 에만 준다.

**동기화가 아니라 프레임 예산이다.** `topic_tools throttle` 은 라이다 스윕을
전혀 모르는 단순 레이트 리미터다. 실측 간격이 100~200ms 로 흔들린다 (30Hz 입력을
100ms 창으로 자르면 주기가 안 나눠떨어져서 가끔 한 주기를 통째로 건너뛴다).

대신 메시지를 손대지 않고 그대로 다시 내보낸다. 그래서 `header.stamp` 이 원본
촬영 시각으로 남고, 실제 시간 정렬은 SLAM 쪽이 `img_time_offset`(Kalibr 측정값)
으로 한다.

10Hz 로 잡은 근거는 `camera.launch.py` 주석에 있다 — FAST-LIVO2 논문의 모든
실험이 10Hz 카메라 + 10Hz 라이다였고, Hilti 에서는 40Hz 카메라를 10Hz 로
다운샘플했다. SR-LIVO(RA-L 2023)는 회전형 라이다에 대해 "스윕 주기의 최대 2배"
라고 못 박는다. 회전 스캔의 시간 조각은 부분표본이 아니라 방위각 쐐기이기
때문이다.

**인지 스택은 이 토픽을 쓰지 않는다.** 30Hz 계약 토픽을 쓴다.

## 파라미터

| 이름 | 타입 | 기본값 | 설명 |
|---|---|---|---|
| `velodyne_ip` | string | 192.168.1.201 | VLP-16 IP 주소 (`lidar.launch.py`) |
| `enable_depth` | bool | true | D435 깊이 + 컬러 정렬 깊이 (`camera.launch.py`) |
| `color_profile` | string | 640x480x30 | D435 컬러 해상도/주기 (`camera.launch.py`) |
| `vectornav_port` | string | /dev/ttyUSB0 | VN-100 시리얼 포트 (`imu.launch.py`) |
| `vectornav_baud` | int | 921600 | 115200 으로는 100Hz 가 안 나온다 (`imu.launch.py`) |
| `imu_rate_divisor` | int | 8 | 800Hz / divisor. 8 → 100Hz, 4 → 200Hz (`imu.launch.py`) |

기본값은 각 launch 파일 한 곳에만 둔다. 상위 런치가 다시 선언해서 넘기지
않는다 — 두 군데로 갈라지면 조용히 어긋난다.

## 알려진 함정

**D435 `global_time_enabled` 는 False 로 둬야 한다.** 이 장비의 펌웨어
5.12.7.150 에서 하드웨어 타임스탬프 조회(UVC XU control)가 실패한다. 커널 로그에
`GET_CUR ... -32` 가 찍히고 드라이버가 모든 프레임을 버려서, 노드는 뜨는데
아무것도 발행하지 않는다. 스탬프는 호스트 시계(도착 시각)로 찍히며 촬영보다
30~100ms 늦다. 그 오프셋은 Kalibr `--time-calibration` 으로 측정한다.

**RealSense 노드만 `LD_LIBRARY_PATH` 에서 bunker_ws 를 걷어낸다.** 이 기계에
OpenCV 가 4.5(apt)와 4.10(/usr/local) 두 벌 있고, bunker_ws 의 cv_bridge 가
4.10 으로 빌드돼 있다. realsense2_camera_node 는 4.5 바이너리라 4.10 cv_bridge 를
집으면 `/compressed` 나 `/theora` 를 누가 구독하는 순간 segfault 한다. bunker_ws 를
전역에서 빼면 안 된다 — `fastlivo_mapping` 은 4.10 바이너리라 그쪽이 필요하다.
서로 다른 프로세스이므로 각자 맞는 것을 쓰면 된다.
