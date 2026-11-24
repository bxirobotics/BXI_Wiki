---
seo_title: "BXI 电机 MIT 回复帧与 AUX 轮询反馈解析"
description: "查阅 BXI 电机 MIT 回复帧的通用解析规则，分别了解旧版 11 项 AUX 轮询与 1.5.5 的 13 项轮询、编码器位置反馈和状态码。"
---

# MIT 轮询回复说明

电机收到有效 MIT 控制帧后返回一帧状态反馈。开启 `mit_aux_enable` 后，最后两个字节携带 AUX 数据。先核对设备的软件版本和配置版本，再查阅第 5 节对应的轮询格式。

| 适用固件 | 每轮回复数 | 轮询 ID | 单项更新频率 |
| --- | ---: | --- | --- |
| 采用旧版 11 项轮询的固件 | 11 | `0x0..0x9`、`0xF` | MIT 回复频率 ÷ 11 |
| 软件 `1.5.5`，配置 `1.5` | 13 | `0x0..0x9`、`0xA`、`0xB`、`0xF` | MIT 回复频率 ÷ 13 |

除特别说明外，本文中的 CAN ID、数据字节、原始值和示例数值均使用十六进制。物理量、频率和单位换算结果会按十进制标出。

## 1. 使用前确认

MIT 回复由上位机发送 MIT 控制帧触发。电机会响应下面两类控制帧：

| 控制帧 CAN ID | 说明 |
| --- | --- |
| `can_id` | 发给当前电机的单播 MIT 控制帧，包含 8 字节控制块 |
| `0x7FF` | 广播 MIT 控制帧，须包含当前 `can_id` 对应的完整 8 字节控制块 |

电机回复帧使用 `master_id` 作为 CAN ID。默认情况下：

```text
master_id = can_id | 0x010
```

例如 `can_id=1` 时，默认 `master_id=0x11`。上位机按设备实际配置的 `master_id` 接收回复。读写方法见[电机寄存器通信协议](register_protocol.md)。

!!! warning

    多电机同时使用 MIT 轮询时，应保证各电机的 `master_id` 不冲突。否则多个电机可能使用同一个 CAN ID 回复，上位机无法可靠区分来源。

## 2. MIT 回复帧格式

MIT 回复帧长度固定为 8 字节：

| 字段 | 内容 |
| --- | --- |
| CAN ID | `master_id` |
| DLC | `8` |
| `data[0]` | 当前电机 `can_id` |
| `data[1..5]` | 普通电机的位置、速度、扭矩反馈，夹爪的位置、速度、力反馈 |
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

下表列出普通电机的编码范围。按设备实际配置还原物理量。夹爪使用 mm、mm/s 和 N，其编码范围见[夹爪通信协议](../grippers/communication.md)。

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

## 4. AUX 轮询回复解析

`mit_aux_enable` 控制 MIT 回复最后两个字节：

```text
mit_aux_enable = 0 -> 温度回复：data[6]=NTC1，data[7]=NTC2，均为 8 bit 编码
mit_aux_enable = 1 -> AUX 轮询：data[6..7] 携带 aux_id + payload
```

支持 AUX 的固件可通过 `mit_aux_enable` 切换回复模式。写入 `1` 启用 AUX，写入 `0` 恢复温度回复。寄存器地址、参数类型与访问权限见[对应版本的寄存器表](register_maps/index.md)。

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

上位机逐帧读取 `aux_id`，再按对应规则解析 `payload`，即可兼容两种轮询长度。

## 5. AUX 轮询顺序和频率

### 5.1 旧版 11 项轮询

本节适用于已确认采用 11 项 AUX 格式的设备。先核对固件的软件版本和配置版本。

1. 按[对应版本的寄存器表](register_maps/index.md)确认 `mit_aux_enable` 的地址、类型和访问权限。写入 `1` 开启 AUX，写入 `0` 恢复温度回复。
2. 发送 [MIT 控制帧](can_communication.md#2-mit-8)，在设备的 `master_id` 上接收 8 字节回复。每次回复由控制帧触发。
3. AUX 开启时，按第 4 节从 `data[6..7]` 提取高 4 位 `aux_id` 和低 12 位 `payload`。温度模式使用第 8 节的解码方式。

采用 11 项格式的固件在 `0x9` 之后发送心跳 `0xF`，然后开始下一轮。

```text
0x0 → 0x1 → 0x2 → 0x3 → 0x4 → 0x5 → 0x6 → 0x7 → 0x8 → 0x9 → 0xF → 0x0
```

一轮包括 10 个反馈项和 1 个心跳项。单项更新频率约为该电机的 MIT 回复频率除以 11。

| MIT 回复频率 | 单项更新频率 |
| ---: | ---: |
| 1000 Hz | 90.9 Hz |
| 500 Hz | 45.5 Hz |
| 100 Hz | 9.1 Hz |

各项按第 6 节解析，位置从第 3 节的基础 `POS` 字段读取。`0xF` 是可回绕的 12 位计数，连续心跳的增量以设备固件为准。

### 5.2 软件 1.5.5（配置 1.5）

#### 启用与接收

1. 在运行中向寄存器 `0x6D` 写入 `1`，类型为 `type=1`（`bool`）。此开关上电为 `0`，每次上电后按需启用。写入 `0` 恢复温度回复。参见 [1.5.5 寄存器表](register_maps/1.5.5.md)。
2. 发送 [MIT 控制帧](can_communication.md#2-mit-8)，在设备的 `master_id` 上接收 8 字节回复。每次回复由控制帧触发。
3. AUX 开启时，按第 4 节从 `data[6..7]` 提取高 4 位 `aux_id` 和低 12 位 `payload`。温度模式下，这两个字节分别为 NTC1 和 NTC2，换算方法见第 8 节。

#### 轮询顺序与心跳

`0xA` 和 `0xB` 在 `0x9` 与心跳 `0xF` 之间发送。每轮共 13 帧，数据无效时也会发送对应项。

```text
0x0 → 0x1 → 0x2 → 0x3 → 0x4 → 0x5 → 0x6 → 0x7 → 0x8 → 0x9 → 0xA → 0xB → 0xF → 0x0
```

单项更新频率约为该电机的 MIT 回复频率除以 13。

| MIT 回复频率 | 单项更新频率 |
| ---: | ---: |
| 1000 Hz | 76.9 Hz |
| 500 Hz | 38.5 Hz |
| 100 Hz | 7.7 Hz |

心跳计数随每帧 AUX 回复递增，按 12 位回绕。连续轮询时，计算同一电机前后两次心跳的计数差 `delta = (current - previous) & 0xFFF`。相邻两次 `0xF` 的 `delta` 为 13。

#### 新增位置反馈 `0xA` 和 `0xB`

| `aux_id` | 位置来源 | 编码范围 | 有效条件 |
| --- | --- | --- | --- |
| `0xA` | ENCI 输入编码器换算 | 普通电机输出轴 `[-max_pos, max_pos]` rad，夹爪位移 `0..90` mm | ENCI 校准有效，且无编码器错误 |
| `0xB` | ENCO 输出编码器测量 | 普通电机输出轴 `[-max_pos, max_pos]` rad | 普通电机配备 AC4754 输出编码器，ENCO 校准有效，最近一次有效采样距今不超过 30 ms |

位置项的有效 `payload` 为 `0x000..0xFFE`（十进制 `0..4094`），分辨率为量程跨度除以 **4094**。条件不满足、位置数值非有限或量程无效时，返回 `0xFFF`。夹爪仍发送 `0xB`，其 `payload` 固定为 `0xFFF`。

```text
普通电机 0xA / 0xB    position_rad = payload × (2 × max_pos) / 4094 − max_pos
夹爪 0xA             position_mm  = payload × 90 / 4094
```

例如最后两个字节为 `A7 FF` 时，`aux_id=0xA`，`payload=0x7FF=2047`。普通电机解析为 `0 rad`，夹爪解析为 `45 mm`。

#### 状态、有效性与配置

- `0x2` 在绕组温度观测器关闭或尚未初始化时返回 `0xFFF`。`0x9` 表示参考电压幅值与可用电压 `v_bus / √3` 的比值，可用电压小于或等于 `0.1 V` 时返回 `0xFFF`。
- `0x7` 沿用第 7 节的位布局。`bit0..3` 还可返回十进制 `11`（回差测试 `BACKLASH`）、`12`（老化测试 `AGING`）和 `13`（工厂测试 `FACTORY`），具体取决于设备与固件功能。夹爪固件的 `bit6` 为 0。普通电机以 `0xB` 的 `payload` 判断 ENCO 位置是否有效。
- 普通电机在电流测试模式下通过 `TOR` 返回 q 轴电流（A）。回差测试时，三个基础反馈字段依次为 ENCI 单圈位置、ENCO 单圈位置及位置差，单位均为 rad。
- 通过寄存器写入 `can_id` 时，`master_id` 保持原值。上位机按实际配置的 `master_id` 接收回复。

## 6. AUX 数据解析

以下 11 项由两种轮询格式共用。`0xA` 和 `0xB` 的换算见第 5.2 节。

| `aux_id` | 数据 | `payload` 解析 | 通信范围 | 分辨率 |
| ---: | --- | --- | --- | --- |
| `0x0` | NTC1 温度 | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 °C | 0.1 °C |
| `0x1` | NTC2 温度 | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 °C | 0.1 °C |
| `0x2` | 估计绕组温度 | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 °C | 0.1 °C |
| `0x3` | 总线电压 `v_bus` | `v_bus = payload / 10.0` | 0.0..100.0 V | 0.1 V |
| `0x4` | 估计母线电流 | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x5` | q 轴电流（滤波后） | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x6` | d 轴电流（滤波后） | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x7` | 程序状态和运行标志 | 见第 7 节位定义 | `0x000..0xFFF` | 位字段 |
| `0x8` | 温控降额系数 | `coeff = payload / 1000.0` | 0.000..1.000 | 0.001 |
| `0x9` | 电压利用率 | `util = payload / 1000.0` | 0.000..2.000 | 0.001 |
| `0xF` | 心跳计数 | `heartbeat = payload` | 0..4095，循环 | 1 |

对于温度、电压、电流和系数等数值项，`payload=0xFFF` 表示数据无效或设备不支持该项。状态字 `0x7` 按位解析，心跳 `0xF` 的 `0xFFF` 是正常计数值。超出编码范围的数值会被限制到端点。

### 换算示例

把有效的 `payload` 作为无符号整数代入对应公式，物理量按十进制计算。

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

`bit6` 为 ENCO 校准标志。下面列出两种格式共用的 `FSM state`，状态码用十进制表示。1.5.5 的测试状态码见第 5.2 节。

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
