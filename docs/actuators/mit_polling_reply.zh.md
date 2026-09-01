# MIT 轮询回复说明

本文说明 BXI 电机在 MIT 模式下的回复帧格式，以及 `mit_aux_enable` 打开后的 AUX 轮询回复解析方式。上位机周期发送 MIT 控制帧后，电机会返回一帧状态反馈；AUX 轮询数据复用回复帧最后两个字节。

除特别说明外，本文中的 CAN ID、数据字节、原始值和示例数值均使用十六进制。物理量、频率和单位换算结果会按十进制标出。

## 1. 使用前确认

MIT 回复由上位机发送 MIT 控制帧触发。电机会响应下面两类控制帧：

| 控制帧 CAN ID | 说明 |
| --- | --- |
| `can_id` | 发给当前电机的单播 MIT 控制帧 |
| `0x7FF` | 广播 MIT 控制帧，电机按自身 `can_id` 取对应的 8 字节控制块 |

电机回复帧使用 `master_id` 作为 CAN ID。默认情况下：

```text
master_id = can_id | 0x010
```

例如 `can_id=1` 时，默认 `master_id=0x11`，上位机应接收 CAN ID 为 `0x11` 的回复帧。修改 `can_id` 时，程序默认会同步更新 `master_id`；也可以通过寄存器单独修改 `master_id`。寄存器命令和寄存器表选择见“电机寄存器通信协议”和对应版本的寄存器表。

!!! warning

    多电机同时使用 MIT 轮询时，应保证各电机的 `master_id` 不冲突。否则多个电机可能使用同一个 CAN ID 回复，上位机无法可靠区分来源。

## 2. MIT 回复帧格式

MIT 回复帧长度固定为 8 字节：

| 字段 | 内容 |
| --- | --- |
| CAN ID | `master_id` |
| DLC | `8` |
| `data[0]` | 当前电机 `can_id` |
| `data[1..5]` | 位置、速度、扭矩反馈 |
| `data[6..7]` | 默认温度反馈；打开 `mit_aux_enable` 后为 AUX 轮询数据 |

字节布局如下：

| 回复帧 | `data[0]` | `data[1]` | `data[2]` | `data[3]` | `data[4]` | `data[5]` | `data[6]` | `data[7]` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mit_aux_enable=0` | `ID` | `POS[15:8]` | `POS[7:0]` | `VEL[11:4]` | `VEL[3:0]` 和 `TOR[11:8]` | `TOR[7:0]` | `NTC1` | `NTC2` |
| `mit_aux_enable=1` | `ID` | `POS[15:8]` | `POS[7:0]` | `VEL[11:4]` | `VEL[3:0]` 和 `TOR[11:8]` | `TOR[7:0]` | `aux[15:8]` | `aux[7:0]` |

这里的位置、速度、扭矩和 AUX 都是按位段拼接。具体拼接方式见文末“位段解析说明”。

## 3. 基础反馈解析

先从 `data[1..5]` 解析出原始值：

```text
id_raw  = data[0]
pos_raw = (data[1] << 8) | data[2]
vel_raw = (data[3] << 4) | (data[4] >> 4)
tor_raw = ((data[4] & 0x0F) << 8) | data[5]
```

再按线性映射还原物理量：

```text
value = raw * (max - min) / ((1 << bits) - 1) + min
```

各字段使用的范围如下。范围值来自电机配置，不同型号或配置可能不同，解析前建议读取对应配置或查看对应版本寄存器表。

| 字段 | 位宽 | 默认范围 |
| --- | ---: | --- |
| `POS` | 16 bit | `[-max_pos, max_pos]`，默认 `[-12.5, 12.5]` rad |
| `VEL` | 12 bit | `[-max_vel, max_vel]`，默认 `[-45.0, 45.0]` rad/s |
| `TOR` | 12 bit | `[-max_tor, max_tor]`，默认值随电机型号不同 |

常用解析公式：

```text
position_rad = uint_to_float(pos_raw, -max_pos, max_pos, 16)
velocity_rad_s = uint_to_float(vel_raw, -max_vel, max_vel, 12)
torque_Nm = uint_to_float(tor_raw, -max_tor, max_tor, 12)
```

!!! note

    正常运行时 `TOR` 表示扭矩反馈。打开电流测试相关功能时，该字段可能被程序用于返回 q 轴电流，具体以当前程序功能状态为准。

## 4. AUX 轮询回复解析

`mit_aux_enable` 控制 MIT 回复最后两个字节：

```text
mit_aux_enable = 0 -> 旧协议：data[6]=NTC1，data[7]=NTC2，均为 8 bit 编码
mit_aux_enable = 1 -> AUX 轮询：data[6..7] 携带 aux_id + payload
```

`mit_aux_enable` 上电默认关闭，且不保存到 Flash。需要 AUX 轮询数据时，上位机需要在本次运行中写入 `mit_aux_enable=1`。当前查看到的程序中该配置项地址为 `0x6D`，不同配置版本仍应以对应寄存器表为准。

打开后，`data[6..7]` 解析为一个 16 bit AUX 字段：

```text
aux = (data[6] << 8) | data[7]
aux_id = (aux >> 12) & 0x0F
payload = aux & 0x0FFF
```

等价拆法：

```text
aux_id = data[6] >> 4
payload = ((data[6] & 0x0F) << 8) | data[7]
```

不要按“第几帧”固定判断数据类型；每帧都应先解析 `aux_id`，再按 `aux_id` 解释 `payload`。

## 5. AUX 轮询顺序和频率

AUX ID 按下面顺序轮询：

```text
0x0 -> 0x1 -> 0x2 -> 0x3 -> 0x4 -> 0x5 -> 0x6 -> 0x7 -> 0x8 -> 0x9 -> 0xF -> 0x0
```

AUX 总频率等于 MIT 回复频率；单项更新频率约为 MIT 回复频率除以 11。

| MIT 回复频率 | 单项更新频率 |
| ---: | ---: |
| 1000 Hz | 90.9 Hz |
| 500 Hz | 45.5 Hz |
| 100 Hz | 9.1 Hz |

## 6. AUX 数据解析

| `aux_id` | 数据 | `payload` 解析 | 通信范围 | 分辨率 |
| ---: | --- | --- | --- | --- |
| `0x0` | NTC1 温度 | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 C | 0.1 C |
| `0x1` | NTC2 温度 | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 C | 0.1 C |
| `0x2` | 绕组温度观测器 | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 C | 0.1 C |
| `0x3` | 总线电压 `v_bus` | `v_bus = payload / 10.0` | 0.0..100.0 V | 0.1 V |
| `0x4` | 母线电流 `i_bus_filt` | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x5` | q 轴电流 `i_q_filt` | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x6` | d 轴电流 `i_d_filt` | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x7` | 程序状态和运行标志 | 见下方 bit 定义 | `0x000..0xFFF` | bitfield |
| `0x8` | 温控降额系数 `temper_coefficient` | `coeff = payload / 1000.0` | 0.000..1.000 | 0.001 |
| `0x9` | 电压利用率 | `util = payload / 1000.0` | 0.000..2.000 | 0.001 |
| `0xF` | 心跳计数 | `heartbeat = payload` | 0..4095，循环 | 1 |

`payload = 0xFFF` 表示该数据无效或当前程序不支持。心跳 `0xF` 例外，因为它正常会循环到 `0xFFF`。

解析 `payload` 时，先通过 `aux_id` 判断数据类型，再把 `payload` 作为无符号整数代入对应公式。表中的除法、偏移量和单位换算使用十进制计算。

温度类数据包括 `aux_id=0x0`、`0x1`、`0x2`：

```text
payload = 0x02BC = 700
temp_C = 700 / 10.0 - 30.0 = 40.0 C
```

电压数据 `aux_id=0x3`：

```text
payload = 0x0F0 = 240
v_bus = 240 / 10.0 = 24.0 V
```

电流类数据包括 `aux_id=0x4`、`0x5`、`0x6`：

```text
payload = 0x05DC = 1500
current_A = 1500 / 10.0 - 150.0 = 0.0 A
```

系数类数据包括 `aux_id=0x8` 和 `0x9`：

```text
payload = 0x02EE = 750
coeff = 750 / 1000.0 = 0.750
util = 750 / 1000.0 = 0.750
```

心跳 `aux_id=0xF` 不需要单位换算，`payload` 就是当前心跳计数。该计数会递增并在 12 bit 范围内循环，可用于判断 MIT 回复是否持续更新。

## 7. 状态字 `0x7`

当 `aux_id=0x7` 时，`payload` 为状态字：

```text
bit0..3   FSM state
bit4      FOC armed
bit5      ENCI calib_valid
bit6      ENCO calib_valid
bit7      field_weaken_mode
bit8      mit_mode
bit9..11  control_mode
```

`bit6` 与外部输出编码器有关，在不支持该硬件或功能的程序中可能始终为 0。

`FSM state` 常见取值：

```text
0  STARTUP
1  MENU
2  MOTOR
3  ENCI_AUTO
4  ENCI
5  ENCO
6  ENCI_SLS_AUTO
7  SETUP
8  ERROR
9  OPEN
10 SLS
```

## 8. 默认协议温度解析

当 `mit_aux_enable=0` 时，`data[6]` 和 `data[7]` 不是 AUX 字段，而是两个 8 bit 温度值：

```text
ntc1_C = data[6] * 180.0 / 255.0 - 30.0
ntc2_C = data[7] * 180.0 / 255.0 - 30.0
```

这种模式下只能从 MIT 回复直接得到 NTC1 和 NTC2 温度；其他 AUX 数据需要打开 `mit_aux_enable` 后读取。

## 9. 解析示例

假设收到一帧：

```text
11#017FFF7FF7FF30F0
```

其中 CAN ID `0x11` 是 `master_id`，数据拆开为：

```text
data[0] = 0x01
data[1] = 0x7F
data[2] = 0xFF
data[3] = 0x7F
data[4] = 0xF7
data[5] = 0xFF
data[6] = 0x30
data[7] = 0xF0
```

基础反馈原始值为：

```text
pos_raw = 0x7FFF
vel_raw = 0x7FF
tor_raw = 0x7FF
```

如果 `mit_aux_enable=1`，最后两个字节解析为：

```text
aux_id = 0x3
payload = 0x0F0
```

`aux_id=0x3` 表示总线电压，所以：

```text
v_bus = 0x0F0 / 10.0 = 24.0 V
```

## 10. 位段解析说明

MIT 回复帧中的 `POS`、`VEL`、`TOR` 和 `aux` 使用高位在前的位段拼接方式。解析时应按位移和掩码恢复原始值。

例如 `data[6]=0x30`、`data[7]=0xF0` 时：

```text
aux = (0x30 << 8) | 0xF0 = 0x30F0
aux_id = (0x30F0 >> 12) & 0x0F = 0x3
payload = 0x30F0 & 0x0FFF = 0x0F0
```

再按 `aux_id` 对应的公式解析 `payload`，即可得到实际物理量或状态字段。
