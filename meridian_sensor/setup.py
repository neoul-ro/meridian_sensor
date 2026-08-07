import os
from glob import glob

from setuptools import setup

package_name = 'meridian_sensor'

setup(
    name=package_name,
    version='0.1.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        (os.path.join('share', package_name, 'launch'), glob('launch/*.launch.py')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='juyoung020',
    maintainer_email='151780134+juyoung020@users.noreply.github.com',
    description='Sensor driver launches for the Meridian robot',
    license='MIT',
)
