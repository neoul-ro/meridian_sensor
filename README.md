# meridian_sensor

Replays a TUM RGB-D sequence as `meridian_msgs/RGBDFrame`.

## I/O

| Topic | Type | Direction |
|---|---|---|
| /rgbd_frame | meridian_msgs/RGBDFrame | pub |

## Parameters

| Name | Type | Default | Description |
|---|---|---|---|
| dataset_dir | string | /home/adas/yun/meridian_ws/data/rgbd_dataset_freiburg1_xyz | TUM RGB-D sequence directory (must contain rgb.txt, depth.txt, and image files) |
| rate_hz | double | 10.0 | Playback rate for the replay timer |
| loop | bool | true | Restart from the first frame after reaching the end of the sequence |
| max_pair_dt | double | 0.02 | Max seconds between an rgb and depth timestamp to associate them |
| calibration_id | int | 1 | Calibration id stamped into each published RGBDFrame |

## Run

```
ros2 run meridian_sensor sensor_node
```
