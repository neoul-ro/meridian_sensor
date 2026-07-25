from setuptools import find_packages, setup

package_name = 'meridian_sensor'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='blu-y',
    maintainer_email='a_o@kakao.com',
    description='RGB-D dataset replay node for the Meridian perception pipeline.',
    license='TODO',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'sensor_node = meridian_sensor.sensor_node:main',
        ],
    },
)
