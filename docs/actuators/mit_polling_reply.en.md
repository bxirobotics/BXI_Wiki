# MIT Polling Reply Guide

This page describes the BXI motor MIT-mode reply frame and the AUX polling reply format enabled by `mit_aux_enable`. After the host sends MIT control frames periodically, the motor returns one status frame for each valid control frame; AUX polling data reuses the last two bytes of that reply frame.

Unless otherwise noted, CAN IDs, data bytes, raw values, and example values in this page are hexadecimal. Physical values, frequencies, and unit conversion results are shown in decimal.

## 1. Check Before Use

MIT replies are triggered by MIT control frames from the host. The motor responds to these control frame IDs:

| Control frame CAN ID | Description |
| --- | --- |
| `can_id` | Unicast MIT control frame for the current motor |
| `0x7FF` | Broadcast MIT control frame; the motor reads its own 8-byte control block according to `can_id` |

The motor reply frame uses `master_id` as its CAN ID. By default:

```text
master_id = can_id | 0x010
```

For example, when `can_id=1`, the default `master_id=0x11`, so the host should receive reply frames with CAN ID `0x11`. When `can_id` is changed, the program normally updates `master_id` together with it. `master_id` can also be changed independently through registers. See "Motor Register Communication Protocol" and the register map for the matching version for register commands and register selection.

!!! warning

    When polling multiple motors in MIT mode, make sure their `master_id` values do not conflict. Otherwise, multiple motors may reply with the same CAN ID and the host cannot reliably distinguish the sources.

## 2. MIT Reply Frame Format

The MIT reply frame is always 8 bytes:

| Field | Content |
| --- | --- |
| CAN ID | `master_id` |
| DLC | `8` |
| `data[0]` | Current motor `can_id` |
| `data[1..5]` | Position, velocity, and torque feedback |
| `data[6..7]` | Temperature feedback by default; AUX polling data when `mit_aux_enable` is enabled |

The byte layout is:

| Reply frame | `data[0]` | `data[1]` | `data[2]` | `data[3]` | `data[4]` | `data[5]` | `data[6]` | `data[7]` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `mit_aux_enable=0` | `ID` | `POS[15:8]` | `POS[7:0]` | `VEL[11:4]` | `VEL[3:0]` and `TOR[11:8]` | `TOR[7:0]` | `NTC1` | `NTC2` |
| `mit_aux_enable=1` | `ID` | `POS[15:8]` | `POS[7:0]` | `VEL[11:4]` | `VEL[3:0]` and `TOR[11:8]` | `TOR[7:0]` | `aux[15:8]` | `aux[7:0]` |

Position, velocity, torque, and AUX are packed as bit fields with the high bits first. See the final "Bit-Field Parsing Notes" section.

## 3. Basic Feedback Parsing

First parse the raw values from `data[1..5]`:

```text
id_raw  = data[0]
pos_raw = (data[1] << 8) | data[2]
vel_raw = (data[3] << 4) | (data[4] >> 4)
tor_raw = ((data[4] & 0x0F) << 8) | data[5]
```

Then convert raw values back to physical values with linear mapping:

```text
value = raw * (max - min) / ((1 << bits) - 1) + min
```

The ranges below come from motor configuration. They may differ between motor models or configurations, so read the related configuration values or check the register map for the matching version before parsing.

| Field | Width | Default range |
| --- | ---: | --- |
| `POS` | 16 bit | `[-max_pos, max_pos]`, default `[-12.5, 12.5]` rad |
| `VEL` | 12 bit | `[-max_vel, max_vel]`, default `[-45.0, 45.0]` rad/s |
| `TOR` | 12 bit | `[-max_tor, max_tor]`, default value depends on the motor model |

Common parsing formulas:

```text
position_rad = uint_to_float(pos_raw, -max_pos, max_pos, 16)
velocity_rad_s = uint_to_float(vel_raw, -max_vel, max_vel, 12)
torque_Nm = uint_to_float(tor_raw, -max_tor, max_tor, 12)
```

!!! note

    In normal operation, `TOR` is torque feedback. When current-test functions are enabled, the program may use this field to return q-axis current instead. Use the current program state as the final reference.

## 4. AUX Polling Reply Parsing

`mit_aux_enable` controls the last two bytes of the MIT reply:

```text
mit_aux_enable = 0 -> legacy protocol: data[6]=NTC1, data[7]=NTC2, both 8-bit encoded
mit_aux_enable = 1 -> AUX polling: data[6..7] carry aux_id + payload
```

`mit_aux_enable` is disabled by default after power-on and is not saved to Flash. To receive AUX polling data, the host must write `mit_aux_enable=1` for the current run. In the currently checked programs, this configuration item is at `0x6D`; for different configuration versions, use the matching register map as the final reference.

When enabled, `data[6..7]` is parsed as one 16-bit AUX field:

```text
aux = (data[6] << 8) | data[7]
aux_id = (aux >> 12) & 0x0F
payload = aux & 0x0FFF
```

Equivalent split:

```text
aux_id = data[6] >> 4
payload = ((data[6] & 0x0F) << 8) | data[7]
```

Do not infer the data type from the frame index. Parse `aux_id` in every frame, then interpret `payload` according to that `aux_id`.

## 5. AUX Polling Order and Rate

AUX IDs rotate in this order:

```text
0x0 -> 0x1 -> 0x2 -> 0x3 -> 0x4 -> 0x5 -> 0x6 -> 0x7 -> 0x8 -> 0x9 -> 0xF -> 0x0
```

The total AUX rate equals the MIT reply rate. Each item updates at roughly the MIT reply rate divided by 11.

| MIT reply rate | Single item rate |
| ---: | ---: |
| 1000 Hz | 90.9 Hz |
| 500 Hz | 45.5 Hz |
| 100 Hz | 9.1 Hz |

## 6. AUX Data Parsing

| `aux_id` | Data | `payload` parsing | Communication range | Resolution |
| ---: | --- | --- | --- | --- |
| `0x0` | NTC1 temperature | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 C | 0.1 C |
| `0x1` | NTC2 temperature | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 C | 0.1 C |
| `0x2` | Winding temperature observer | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 C | 0.1 C |
| `0x3` | Bus voltage `v_bus` | `v_bus = payload / 10.0` | 0.0..100.0 V | 0.1 V |
| `0x4` | Bus current `i_bus_filt` | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x5` | q-axis current `i_q_filt` | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x6` | d-axis current `i_d_filt` | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x7` | Program state and runtime flags | See bit definitions below | `0x000..0xFFF` | bitfield |
| `0x8` | Thermal derating coefficient `temper_coefficient` | `coeff = payload / 1000.0` | 0.000..1.000 | 0.001 |
| `0x9` | Voltage utilization | `util = payload / 1000.0` | 0.000..2.000 | 0.001 |
| `0xF` | Heartbeat counter | `heartbeat = payload` | 0..4095, wraps | 1 |

`payload = 0xFFF` means the data is invalid or unsupported by the current program. Heartbeat `0xF` is the exception, because it naturally wraps through `0xFFF`.

When parsing `payload`, first use `aux_id` to identify the data type, then treat `payload` as an unsigned integer and apply the corresponding formula. The divisions, offsets, and unit conversions in the table are decimal calculations.

Temperature data includes `aux_id=0x0`, `0x1`, and `0x2`:

```text
payload = 0x02BC = 700
temp_C = 700 / 10.0 - 30.0 = 40.0 C
```

Voltage data uses `aux_id=0x3`:

```text
payload = 0x0F0 = 240
v_bus = 240 / 10.0 = 24.0 V
```

Current data includes `aux_id=0x4`, `0x5`, and `0x6`:

```text
payload = 0x05DC = 1500
current_A = 1500 / 10.0 - 150.0 = 0.0 A
```

Coefficient data includes `aux_id=0x8` and `0x9`:

```text
payload = 0x02EE = 750
coeff = 750 / 1000.0 = 0.750
util = 750 / 1000.0 = 0.750
```

Heartbeat `aux_id=0xF` does not need unit conversion. `payload` is the current heartbeat count. It increments and wraps in the 12-bit range, so it can be used to check whether MIT replies are still updating.

## 7. Status Word `0x7`

When `aux_id=0x7`, `payload` is a status word:

```text
bit0..3   FSM state
bit4      FOC armed
bit5      ENCI calib_valid
bit6      ENCO calib_valid
bit7      field_weaken_mode
bit8      mit_mode
bit9..11  control_mode
```

`bit6` is related to the external output encoder. It may remain 0 in programs that do not support that hardware or function.

Common `FSM state` values:

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

## 8. Default Protocol Temperature Parsing

When `mit_aux_enable=0`, `data[6]` and `data[7]` are not an AUX field. They are two 8-bit temperature values:

```text
ntc1_C = data[6] * 180.0 / 255.0 - 30.0
ntc2_C = data[7] * 180.0 / 255.0 - 30.0
```

In this mode, the MIT reply directly provides only NTC1 and NTC2 temperatures. Other AUX data requires `mit_aux_enable` to be enabled.

## 9. Parsing Example

Assume this reply is received:

```text
11#017FFF7FF7FF30F0
```

CAN ID `0x11` is `master_id`, and the data bytes are:

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

The basic raw feedback values are:

```text
pos_raw = 0x7FFF
vel_raw = 0x7FF
tor_raw = 0x7FF
```

If `mit_aux_enable=1`, the last two bytes parse as:

```text
aux_id = 0x3
payload = 0x0F0
```

`aux_id=0x3` means bus voltage, so:

```text
v_bus = 0x0F0 / 10.0 = 24.0 V
```

## 10. Bit-Field Parsing Notes

`POS`, `VEL`, `TOR`, and `aux` in MIT reply frames are packed as bit fields with high bits first. Restore raw values with shifts and masks.

For example, when `data[6]=0x30` and `data[7]=0xF0`:

```text
aux = (0x30 << 8) | 0xF0 = 0x30F0
aux_id = (0x30F0 >> 12) & 0x0F = 0x3
payload = 0x30F0 & 0x0FFF = 0x0F0
```

Then parse `payload` with the formula for the corresponding `aux_id` to get the physical value or status field.
