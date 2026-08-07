"""VectorNav VN-100 driver only -> /vectornav/imu (100Hz)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('vectornav_port', default_value='/dev/ttyUSB0'),
        # 100Hz full binary output needs more than 115200 baud (sensor rejects
        # with InsufficientBaudRate); VN-100 supports up to 921600.
        DeclareLaunchArgument('vectornav_baud', default_value='921600'),
        # VN-100 internal rate is 800Hz; 800/8 = 100Hz IMU output (default).
        # Allan-variance recording can use 200Hz with imu_rate_divisor:=4
        # (bandwidth fits at 921600 baud).
        DeclareLaunchArgument('imu_rate_divisor', default_value='8'),
        Node(
            package='vectornav',
            executable='vectornav',
            name='vectornav',
            parameters=[{
                'port': LaunchConfiguration('vectornav_port'),
                'baud': ParameterValue(
                    LaunchConfiguration('vectornav_baud'), value_type=int),
                'BO1.rateDivisor': ParameterValue(
                    LaunchConfiguration('imu_rate_divisor'), value_type=int),
                # Output on serial port 1 only. Default BOTH also pushes 100Hz
                # to the unused second UART (115200) -> InsufficientBaudRate.
                'BO1.asyncMode': 1,
            }],
            output='screen',
        ),
        Node(
            package='vectornav',
            executable='vn_sensor_msgs',
            name='vn_sensor_msgs',
            output='screen',
        ),
    ])
