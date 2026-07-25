import os

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from sensor_msgs.msg import CameraInfo, Image

TUM_DEPTH_SCALE = 5000.0


def _read_tum_list(path):
    # TUM format: "timestamp filename" per line, '#' lines are comments.
    entries = []
    with open(path, 'r') as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split()
            entries.append((float(parts[0]), parts[1]))
    return entries


class MeridianSensor(Node):

    def __init__(self):
        super().__init__('meridian_sensor')

        self.declare_parameter('dataset_dir', '/home/adas/yun/meridian_ws/data/rgbd_dataset_freiburg1_xyz')
        self.declare_parameter('rate_hz', 10.0)
        self.declare_parameter('loop', True)
        self.declare_parameter('max_pair_dt', 0.02)
        # TUM freiburg1 default intrinsics
        self.declare_parameter('fx', 525.0)
        self.declare_parameter('fy', 525.0)
        self.declare_parameter('cx', 319.5)
        self.declare_parameter('cy', 239.5)

        self.dataset_dir = self.get_parameter('dataset_dir').value
        self.rate_hz = self.get_parameter('rate_hz').value
        self.loop = self.get_parameter('loop').value
        self.max_pair_dt = self.get_parameter('max_pair_dt').value
        self.fx = self.get_parameter('fx').value
        self.fy = self.get_parameter('fy').value
        self.cx = self.get_parameter('cx').value
        self.cy = self.get_parameter('cy').value

        self.bridge = CvBridge()
        self.pairs = []
        self.index = 0

        qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=10)
        self.rgb_pub = self.create_publisher(Image, '/camera/rgb', qos)
        self.depth_pub = self.create_publisher(Image, '/camera/depth', qos)
        self.info_pub = self.create_publisher(CameraInfo, '/camera/info', qos)

        self.pairs = self._build_pairs()
        self.get_logger().info('meridian_sensor started, %d rgb-depth pairs' % len(self.pairs))

        self.timer = None
        if not self.pairs:
            self.get_logger().error('no rgb-depth pairs available, dataset_dir=%s' % self.dataset_dir)
        else:
            self.timer = self.create_timer(1.0 / self.rate_hz, self._on_timer)

    def _build_pairs(self):
        if not os.path.isdir(self.dataset_dir):
            return []

        rgb_path = os.path.join(self.dataset_dir, 'rgb.txt')
        depth_path = os.path.join(self.dataset_dir, 'depth.txt')
        rgb_list = _read_tum_list(rgb_path)
        depth_list = _read_tum_list(depth_path)

        used_depth = [False] * len(depth_list)
        pairs = []
        for rgb_ts, rgb_file in rgb_list:
            best_j = -1
            best_dt = None
            for j, (depth_ts, depth_file) in enumerate(depth_list):
                if used_depth[j]:
                    continue
                dt = abs(depth_ts - rgb_ts)
                if dt <= self.max_pair_dt and (best_dt is None or dt < best_dt):
                    best_dt = dt
                    best_j = j
            if best_j >= 0:
                used_depth[best_j] = True
                pairs.append((os.path.join(self.dataset_dir, rgb_file),
                              os.path.join(self.dataset_dir, depth_list[best_j][1])))

        return pairs

    def _on_timer(self):
        rgb_path, depth_path = self.pairs[self.index]

        bgr = cv2.imread(rgb_path)
        rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB)
        depth_raw = cv2.imread(depth_path, cv2.IMREAD_UNCHANGED)
        depth_m = depth_raw.astype(np.float32) / TUM_DEPTH_SCALE

        stamp = self.get_clock().now().to_msg()

        rgb_msg = self.bridge.cv2_to_imgmsg(rgb, encoding='rgb8')
        rgb_msg.header.stamp = stamp
        rgb_msg.header.frame_id = 'camera'
        depth_msg = self.bridge.cv2_to_imgmsg(depth_m, encoding='32FC1')
        depth_msg.header.stamp = stamp
        depth_msg.header.frame_id = 'camera'

        info_msg = CameraInfo()
        info_msg.header.stamp = stamp
        info_msg.header.frame_id = 'camera'
        info_msg.width = rgb_msg.width
        info_msg.height = rgb_msg.height
        info_msg.distortion_model = 'plumb_bob'
        info_msg.k = [self.fx, 0.0, self.cx,
                      0.0, self.fy, self.cy,
                      0.0, 0.0, 1.0]
        info_msg.p = [self.fx, 0.0, self.cx, 0.0,
                      0.0, self.fy, self.cy, 0.0,
                      0.0, 0.0, 1.0, 0.0]

        self.rgb_pub.publish(rgb_msg)
        self.depth_pub.publish(depth_msg)
        self.info_pub.publish(info_msg)

        self.get_logger().info('published frame %d/%d' % (self.index + 1, len(self.pairs)),
                                throttle_duration_sec=5.0)

        self.index += 1
        if self.index >= len(self.pairs):
            if self.loop:
                self.index = 0
                self.get_logger().info('reached end of sequence, restarting from index 0')
            else:
                self.get_logger().info('reached end of sequence, stopping')
                self.timer.cancel()


def main():
    rclpy.init()
    node = MeridianSensor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
