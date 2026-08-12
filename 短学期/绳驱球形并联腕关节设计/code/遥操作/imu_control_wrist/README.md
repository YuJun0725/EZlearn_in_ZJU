# ESP32 + IMU 球形腕实时控制

本目录实现下面的数据闭环：

```text
MPU6050 -> ESP32 -> USB 串口 -> 电脑逆运动学
                              |
3 个总线舵机 <- ESP32 <- theta1/theta2/theta3
```

ESP32 只负责采集姿态、收发数据和驱动舵机；逆运动学在电脑上运行。

## 目录

```text
esp32_imu_wrist_realtime/
|-- esp32_firmware/   PlatformIO 固件
|-- pc_host/          电脑端 Python 程序
|-- PROTOCOL.md       串口帧定义
`-- README.md
```

## 当前约定

- 欧拉角顺序：`R = Rz(yaw) Ry(pitch) Rx(roll)`，单位为度。
- 逆解工作模式：`(1, 1, 1)`。
- 几何参数：`ew=-37 deg, ev=0 deg, delta=-90 deg, alpha=90 deg`。
- 舵机零位：位置值 `2048` 对应 `theta=0 deg`。
- `theta` 增大为物理逆时针，所以位置换算为：

  ```text
  servo_position = 2048 - theta_deg * 3 * 4096 / 360
  ```

- 三轴传动比均为 `3:1`：舵机输出轴转 `3 deg`，机构的 `theta` 转 `1 deg`。
- 当前舵机按单圈 `0~4095` 使用且中位为 `2048`，因此机构 theta 限制为 `[-59 deg, 59 deg]`，在舵机两端保留少量余量。
- 电脑端和 ESP32 端都会检查三轴圆周顺序与最小轴间隙；任一检查失败都不会执行目标。
- ESP32 使用同步写命令一次更新三个舵机目标。
- 实时 IMU 帧不要求电脑 ACK；ESP32 对每个舵机目标帧返回 ACK。

## 接线

默认引脚在 `esp32_firmware/include/config.h` 中：

| 设备 | ESP32 引脚/接口 |
|---|---|
| MPU6050 SDA | GPIO 21 |
| MPU6050 SCL | GPIO 22 |
| 舵机总线 RX | GPIO 16 |
| 舵机总线 TX | GPIO 17 |
| 电脑 | ESP32 USB 串口，115200 baud |

舵机应使用独立的合适电源，舵机电源地、ESP32 地和总线转换电路地必须共地。不要用 ESP32 开发板的 5 V 引脚给三个舵机供电。

## 1. 烧录 ESP32

在 VS Code 的 PlatformIO 中打开 `esp32_firmware`，选择 `esp32dev` 环境后执行 Upload；也可以在 PlatformIO 终端运行：

```powershell
cd .\esp32_firmware
pio run -t upload
```

固件依赖 `Adafruit MPU6050`，PlatformIO 首次构建会自动安装。默认 I2C 地址为 `0x68`；如果模块的 AD0 拉高，请把 `config.h` 中地址改为 `0x69`。

MPU6050 上电后会采集 500 次数据估计陀螺仪零偏和初始重力方向，这一秒左右必须保持手持控制器静止。固件会检查角速度和加速度波动；如果校准期间发生运动，电脑会显示 `keep the controller still during calibration`，ESP32 会自动重试，不会使用错误零偏。固件使用相对四元数记录完整的启动参考姿态，因此无论模块正面或反面朝上，初始姿态都会被定义为 `RPY=(0,0,0)`，不会在 `+180/-180 deg` 附近发生欧拉角滤波跳变。

固件默认上电不主动把三个舵机拉回零位，防止机构突然动作。只有收到一帧通过检查的 `theta` 后才会运动。需要上电归零时，可把 `config.h` 中的 `MOVE_TO_ZERO_ON_BOOT` 改为 `true`。

## 2. 安装电脑端依赖

Windows PowerShell：

```powershell
cd .\pc_host
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

树莓派/Linux：

```bash
cd pc_host
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## 3. 先做静态测试

连接 ESP32 后查询串口：

```powershell
python .\main.py --list-ports
```

先不依赖 IMU，手动发送姿态测试逆解、协议和舵机：

```powershell
python .\main.py --port COM5 --pose 20 20 30
```

把 `COM5` 改成实际端口。程序会输出逆解角度，并等待 ESP32 ACK。

为了先检查 IMU 数值和逆解而不让舵机动：

```powershell
python .\main.py --port COM5 --monitor-only
```

## 4. 启动实时控制

确认方向、零位、限位和 `monitor-only` 输出都正确后运行：

```powershell
python .\main.py --port COM5
```

程序始终使用串口中最新的一组 RPY，先进行自适应四元数滤波，再执行逆解和电机角速度/加速度限制，最后以最高 50 Hz 向 ESP32 发目标。按 `Ctrl+C` 停止；停止发送后，舵机保持最后一个目标位置。

实时输出中的字段含义：

```text
RPY raw       MPU6050 原始姿态
filtered      自适应滤波后的目标姿态
theta target  逆解得到的最终电机目标
command       当前周期实际发给 ESP32 的平滑电机角
```

平滑参数位于 `pc_host/config.json`：

| 参数 | 默认值 | 作用 |
|---|---:|---|
| `command_rate_hz` | 50 | 电机目标发送频率 |
| `orientation_filter_min_cutoff_hz` | 3.0 | 静止/慢速时的滤波带宽；越小越稳但延迟越大 |
| `orientation_filter_beta` | 0.025 | 快速转动时自动提高跟手性的程度 |
| `orientation_deadband_deg` | 0.15 | 小于该姿态变化时不更新逆解目标 |
| `theta_max_speed_deg_s` | 90 | 单轴最大指令速度 |
| `theta_max_acceleration_deg_s2` | 360 | 单轴最大指令加速度 |

## 调整位置

- 串口、舵机 ID、舵机方向、零偏、MPU6050 引脚与轴映射：`esp32_firmware/include/config.h`
- `w0/v0/alpha`、工作模式、关节限位、轴间最小间隙：`pc_host/config.json`
- MPU6050 零偏校准、互补滤波和 RPY 计算：`esp32_firmware/src/imu_source.cpp`
- 电脑实时循环：`pc_host/main.py`

如果实际安装后某个舵机方向相反，只修改该轴的 `SERVO_THETA_SIGN`。按你给出的当前物理关系，三个默认值都是 `-1`。

## 一个必须区分的问题

当前代码把 IMU 姿态直接当作腕关节的目标姿态。它适合“手持 IMU/外部姿态源控制腕关节”。

如果 MPU6050 固定在腕关节动平台上，那么它测到的是实际姿态，不是目标姿态。此时“实际姿态 -> 逆解 -> 舵机”只会让机构跟随自己当前的位置，不能自动回到另一个目标。要实现真正的位置闭环，还需要额外输入目标 RPY，并在电脑端增加目标姿态与测量姿态之间的反馈控制器。

另外，MPU6050 没有磁力计。当前代码用陀螺仪积分计算 yaw，因此 yaw 会逐渐漂移；加速度计只能长期修正 roll 和 pitch。需要长期稳定的绝对 yaw 时，应增加磁力计并做九轴融合，或改用能够输出融合姿态的传感器。
