# meridian_sensor

Replays a TUM RGB-D sequence as standard camera topics.

## I/O

| Topic | Type | Direction |
|---|---|---|
| /camera/rgb | sensor_msgs/Image (rgb8) | pub |
| /camera/depth | sensor_msgs/Image (32FC1, meters) | pub |
| /camera/info | sensor_msgs/CameraInfo | pub |

All three topics share the same `header.stamp` per frame.

## Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| dataset_dir | string | /home/adas/yun/meridian_ws/data/rgbd_dataset_freiburg1_xyz | TUM RGB-D sequence directory (must contain rgb.txt, depth.txt, and image files) |
| rate_hz | double | 10.0 | Playback rate for the replay timer |
| loop | bool | true | Restart from the first frame after reaching the end of the sequence |
| max_pair_dt | double | 0.02 | Max seconds between an rgb and depth timestamp to associate them |
| fx | double | 525.0 | Camera intrinsic focal length x |
| fy | double | 525.0 | Camera intrinsic focal length y |
| cx | double | 319.5 | Camera principal point x |
| cy | double | 239.5 | Camera principal point y |

## Run

```
ros2 run meridian_sensor sensor_node
```
