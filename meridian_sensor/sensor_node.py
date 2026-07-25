import os

import cv2
import numpy as np
import rclpy
from cv_bridge import CvBridge
from rclpy.node import Node
from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy

from meridian_msgs.msg import RGBDFrame

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
        self.declare_parameter('calibration_id', 1)

        self.dataset_dir = self.get_parameter('dataset_dir').value
        self.rate_hz = self.get_parameter('rate_hz').value
        self.loop = self.get_parameter('loop').value
        self.max_pair_dt = self.get_parameter('max_pair_dt').value
        self.calibration_id = self.get_parameter('calibration_id').value

        self.bridge = CvBridge()
        self.pairs = []
        self.index = 0

        qos = QoSProfile(reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST, depth=10)
        self.pub = self.create_publisher(RGBDFrame, '/rgbd_frame', qos)

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

        frame = RGBDFrame()
        frame.timestamp = stamp
        frame.rgb = self.bridge.cv2_to_imgmsg(rgb, encoding='rgb8')
        frame.rgb.header.stamp = stamp
        frame.rgb.header.frame_id = 'camera'
        frame.depth_m = self.bridge.cv2_to_imgmsg(depth_m, encoding='32FC1')
        frame.depth_m.header.stamp = stamp
        frame.depth_m.header.frame_id = 'camera'
        frame.calibration_id = self.calibration_id

        self.pub.publish(frame)

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
