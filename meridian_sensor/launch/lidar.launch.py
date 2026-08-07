"""VLP-16 driver only -> /velodyne_points (+ Meridian schema alias /lidar/points)."""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node


def generate_launch_description():
    vlp16_calib = os.path.join(
        get_package_share_directory('velodyne_pointcloud'), 'params', 'VLP16db.yaml')

    return LaunchDescription([
        DeclareLaunchArgument('velodyne_ip', default_value='192.168.1.201'),
        Node(
            package='velodyne_driver',
            executable='velodyne_driver_node',
            name='velodyne_driver',
            parameters=[{
                'model': 'VLP16',
                'device_ip': LaunchConfiguration('velodyne_ip'),
                'rpm': 600.0,
                'port': 2368,
                'frame_id': 'velodyne',
                # 스캔 "시작" 시각으로 스탬프 + 포인트별 양수 오프셋(0~100ms).
                # 기본값(false)은 스캔 끝 스탬프 + 음수 오프셋이라 FAST-LIVO2의
                # scan recombination 가정(시작 스탬프)과 어긋나, 이미지 컷이
                # 빈 배치가 되어 VIO 업데이트 2/3가 헛돈다.
                'timestamp_first_packet': True,
            }],
            output='screen',
        ),
        Node(
            package='velodyne_pointcloud',
            executable='velodyne_transform_node',
            name='velodyne_transform',
            parameters=[{
                'model': 'VLP16',
                'calibration': vlp16_calib,
                'min_range': 0.4,
                'max_range': 130.0,
                'fixed_frame': '',
                'target_frame': '',
                'organize_cloud': False,
            }],
            output='screen',
        ),
        # Meridian 스키마 별칭 (Architecture 문서의 LiDAR Driver 출력).
        # 기존 /velodyne_points는 그대로 두고 이름만 하나 더 발행.
        # lazy: 구독자가 없으면 아무 것도 안 함 (부하 0).
        Node(
            package='topic_tools',
            executable='relay',
            name='lidar_schema_relay',
            parameters=[{
                'input_topic': '/velodyne_points',
                'output_topic': '/lidar/points',
                'lazy': True,
            }],
            output='screen',
        ),
    ])
