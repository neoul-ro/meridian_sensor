"""RealSense D435 driver only -> /camera/camera/color/image_raw.

Also publishes the Meridian schema aliases (Architecture doc, Camera Driver):
  /camera/rgb    <- color/image_raw   (relay)
  /camera/info   <- color/camera_info (relay)
  /camera/depth  <- aligned depth, 16UC1 mm -> 32FC1 m (depth_image_proc)
The native RealSense topics stay untouched.
"""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.conditions import IfCondition
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        # Depth + color-aligned depth on by default (SAM pipeline consumes it).
        DeclareLaunchArgument('enable_depth', default_value='true',
                              description='Enable D435 depth + color-aligned depth'),
        Node(
            package='realsense2_camera',
            executable='realsense2_camera_node',
            name='camera',
            namespace='camera',
            parameters=[{
                'enable_color': True,
                'rgb_camera.color_profile': '848x480x30',
                # Stamp frames with host clock so they align with VLP-16/VN-100.
                'global_time_enabled': True,
                'enable_depth': ParameterValue(
                    LaunchConfiguration('enable_depth'), value_type=bool),
                'align_depth.enable': ParameterValue(
                    LaunchConfiguration('enable_depth'), value_type=bool),
                'enable_infra1': False,
                'enable_infra2': False,
                'enable_sync': True,
            }],
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
