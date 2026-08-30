"""VectorNav VN-100 드라이버만 -> /vectornav/imu (100Hz)."""

from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node
from launch_ros.parameter_descriptions import ParameterValue


def generate_launch_description():
    return LaunchDescription([
        DeclareLaunchArgument('vectornav_port', default_value='/dev/ttyUSB0'),
        # 100Hz 풀 바이너리 출력은 115200 보드로는 안 된다 (센서가
        # InsufficientBaudRate 로 거부한다). VN-100 은 921600 까지 지원한다.
        DeclareLaunchArgument('vectornav_baud', default_value='921600'),
        # VN-100 내부 주기는 800Hz 다. 800/8 = 100Hz IMU 출력(기본값).
        # Allan variance 녹화는 imu_rate_divisor:=4 로 200Hz 를 쓸 수 있다
        # (921600 보드면 대역폭이 감당된다).
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
                # 시리얼 포트 1 로만 출력한다. 기본값 BOTH 는 쓰지도 않는
                # 두 번째 UART(115200)로도 100Hz 를 밀어서 InsufficientBaudRate
                # 가 난다.
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
