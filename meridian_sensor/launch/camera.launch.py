"""RealSense D435 드라이버만 -> /camera/camera/color/image_raw.

Meridian 계약 별칭도 함께 발행한다 (Architecture 문서, Camera Driver 절):
  /camera/rgb    <- color/image_raw   (릴레이)
  /camera/info   <- color/camera_info (릴레이)
  /camera/depth  <- 정렬된 깊이, 16UC1 mm -> 32FC1 m (depth_image_proc)
네이티브 RealSense 토픽은 손대지 않는다.
"""

import os

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def _system_cv_bridge_env():
    """bunker_ws 를 걷어낸 LD_LIBRARY_PATH. RealSense 노드에만 쓴다.

    이 기계에는 OpenCV 가 두 벌 깔려 있다. apt 의 4.5 (ROS Humble 바이너리들이
    링크하는 것)와 /usr/local 의 4.10 (fast_livo 가 링크하는 것). bunker_ws 는
    4.10 으로 빌드한 cv_bridge 를 담고 있고, slam_ws2 의 install/setup.sh 가
    bunker_ws 를 체인 소스하기 때문에 라이브러리 경로에서 시스템 것보다 앞에
    온다.

    realsense2_camera_node 자체는 4.5 바이너리이고 image_transport 플러그인을
    통해 cv_bridge 를 지연 로드한다. 여기서 4.10 cv_bridge 를 집으면 4.10 의
    cv::cvtColor 가 4.5 의 cv::_OutputArray::create 를 부르게 되고 — 구조체
    레이아웃이 다르다 — 누군가 /compressed 나 /theora 토픽을 구독하는 순간
    노드가 segfault 한다. 2026-08-10 gdb 로 확인했고, compressed 와 theora 가
    동일한 백트레이스를 낸다.

    이걸 bunker_ws 를 전역에서 빼는 식으로 고치면 안 된다. fastlivo_mapping 은
    4.10 바이너리라 같은 4.10 cv_bridge 가 있어야 일관성이 맞는다. 서로 다른
    프로세스이므로 각자 맞는 것을 가지면 된다.
    """
    entries = os.environ.get('LD_LIBRARY_PATH', '').split(':')
    kept = [p for p in entries if p and '/bunker_ws/' not in p]
    return ':'.join(kept)


def generate_launch_description():
    return LaunchDescription([
        # 깊이 + 컬러 정렬 깊이를 기본으로 켠다 (SAM 파이프라인이 쓴다).
        DeclareLaunchArgument('enable_depth', default_value='true'),
        # FAST-LIVO2 는 카메라가 라이다 주기로 들어오길 원한다. 논문의 모든 실험이
        # 10 Hz 카메라와 10 Hz 라이다 조합이었고, Hilti 에서는 저자들이 40 Hz 카메라를
        # 10 Hz 로 다운샘플했다 — sync_packages 가 40 Hz 로 자르게 두지 않았다.
        # SR-LIVO (RA-L 2023) 는 회전형 라이다에 대해 이 규칙을 명시한다: 스윕
        # 주기의 최대 2배까지. 회전 스캔의 시간 조각은 부분표본이 아니라 방위각
        # 쐐기이기 때문이다. 우리는 3:1 로 돌리고 있었다.
        # 2026-08-26: 848x480 (16:9) -> 640x480 (4:3). meridian_seg 의 letterbox
        # 는 소스 해상도에서 자동으로 계산되는데, 4:3 이 아니면 /segment_image 가
        # 256x192 가 아니라 256x145 로 나오고 원본 좌표 환산 배율도 2.5 가 아니라
        # 3.3125 가 된다. meridian_seg / meridian_geobuilder 문서가 전부 2.5 를
        # 전제하고 있어서 해상도 쪽을 맞췄다.
        # ! camera_d435.yaml 의 intrinsic 은 848x480 에서 Kalibr 로 잰 값이다.
        #   640x480 은 같은 센서의 다른 판독 모드라 그 값을 그대로 쓸 수 없다.
        # 되돌리려면 '848x480x30' 으로.
        DeclareLaunchArgument('color_profile', default_value='640x480x30'),
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='camera',
            namespace='camera',
            parameters=[{
                'enable_color': True,
                'rgb_camera.color_profile': LaunchConfiguration('color_profile'),
                # 이 장비에서는 False 로 둬야 한다. global time 이 필요로 하는
                # 하드웨어 타임스탬프 조회(UVC XU control)가 펌웨어 5.12.7.150
                # 에서 실패한다 — 커널 로그에 "GET_CUR ... -32" 가 찍히고 그 뒤로
                # 드라이버가 모든 프레임을 버려서, 노드는 뜨는데 아무것도 발행하지
                # 않는다. 스탬프는 여전히 호스트 시계(도착 시각)로 찍히며 촬영보다
                # 30~100ms 늦다. 그 오프셋은 Kalibr 의 --time-calibration 으로
                # 측정한다. 펌웨어를 올린 뒤 True 로 다시 시도해 볼 것.
                'global_time_enabled': False,
                'enable_depth': ParameterValue(
                    LaunchConfiguration('enable_depth'), value_type=bool),
                'align_depth.enable': ParameterValue(
                    LaunchConfiguration('enable_depth'), value_type=bool),
                'enable_infra1': False,
                'enable_infra2': False,
                'enable_sync': True,
            }],
            additional_env={'LD_LIBRARY_PATH': _system_cv_bridge_env()},
            output='screen',
        ),
        # -- SLAM 전용 10 Hz 스트림 --
        # FAST-LIVO2 의 sync_packages 는 이미지 타임스탬프마다 라이다 스윕을 자른다.
        # 회전식 라이다에서 시간 조각은 곧 방위각 쐐기라(preprocess.cpp:390, 3.61 deg/ms),
        # 카메라가 라이다보다 빠르면 LIO 갱신이 360 도가 아니라 쐐기 하나만 보게 된다.
        # 30 Hz 대 10 Hz(3:1)에서는 LIO 갱신의 절반이 빈 조각이었다 -- 3 분에
        # "[ LIO ]: No point!!!" 1,996 회. 카메라 자체를 15 Hz 로 내려보니 8 회로 떨어졌다.
        #
        # 다만 카메라는 30 Hz 로 유지해야 한다(CLIP/인스턴스 파이프라인 등 다른 소비자).
        # 그래서 발행은 30 Hz 그대로 두고, SLAM 이 구독하는 토픽만 여기서 10 Hz 로 솎는다.
        # velodyne16_vn100.yaml 의 common.img_topic 이 이 토픽을 가리킨다.
        #
        # 근거: FAST-LIVO2 논문의 모든 실험이 카메라를 라이다 속도로 맞췄고(Hilti 는
        # 40 Hz 카메라를 10 Hz 로 다운샘플), SR-LIVO(RA-L 2023, arXiv:2312.16800) Sec.V-A 는
        # 회전식 라이다에 대해 "at most twice the frequency of raw LiDAR sweeps" 라고 못박는다.
        Node(
            package='topic_tools',
            executable='throttle',
            name='camera_slam_throttle',
            arguments=['messages', '/camera/camera/color/image_raw', '10.0',
                       '/camera/camera/color/image_slam'],
            output='screen',
        ),
        # -- Meridian 스키마 별칭 (기존 토픽은 그대로, lazy라 구독 전엔 부하 0) --
        Node(
            package='topic_tools',
            executable='relay',
            name='camera_rgb_relay',
            parameters=[{
                'input_topic': '/camera/camera/color/image_raw',
                'output_topic': '/camera/rgb',
                'lazy': True,
            }],
            output='screen',
        ),
        Node(
            package='topic_tools',
            executable='relay',
            name='camera_info_relay',
            parameters=[{
                'input_topic': '/camera/camera/color/camera_info',
                'output_topic': '/camera/info',
                'lazy': True,
            }],
            output='screen',
        ),
        # 스키마는 32FC1(미터), RealSense는 16UC1(밀리미터) -> 공식 변환 노드.
        Node(
            package='depth_image_proc',
            executable='convert_metric_node',
            name='camera_depth_metric',
            condition=IfCondition(LaunchConfiguration('enable_depth')),
            remappings=[
                ('image_raw', '/camera/camera/aligned_depth_to_color/image_raw'),
                ('image', '/camera/depth'),
            ],
            output='screen',
        ),
    ])
