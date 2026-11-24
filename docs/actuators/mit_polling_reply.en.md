---
seo_title: "BXI MIT Motor Reply Frames and AUX Polling"
description: "Decode BXI MIT replies and distinguish the older 11-item AUX format from firmware 1.5.5's 13-item cycle, including ENCI/ENCO positions, validity checks, status words and conversions."
---

# MIT Polling Reply Guide

The motor returns one status frame for each valid MIT control frame. When `mit_aux_enable` is enabled, the last two bytes carry AUX data. Check the device's software and configuration versions before choosing a polling format in section 5.

| Applicable firmware | Replies per cycle | AUX IDs | Update rate per item |
| --- | ---: | --- | --- |
| Firmware using the older 11-item AUX format | 11 | `0x0..0x9`, `0xF` | MIT reply rate ÷ 11 |
| Software `1.5.5`, configuration `1.5` | 13 | `0x0..0x9`, `0xA`, `0xB`, `0xF` | MIT reply rate ÷ 13 |

Unless otherwise noted, CAN IDs, data bytes, raw values, and example values in this page are hexadecimal. Physical values, frequencies, and unit conversion results are shown in decimal.

## 1. Check Before Use

MIT replies are triggered by MIT control frames from the host. The motor responds to these control frame IDs:

| Control frame CAN ID | Description |
| --- | --- |
| `can_id` | Unicast MIT control frame with an 8-byte control block for the current motor |
| `0x7FF` | Broadcast MIT control frame containing the full 8-byte block for the current `can_id` |

The motor reply frame uses `master_id` as its CAN ID. By default:

```text
master_id = can_id | 0x010
```

When `can_id=1`, the default `master_id` is `0x11`. The host receives replies on the device's configured `master_id`. See the [Motor Register Communication Protocol](register_protocol.md) for register commands.

!!! warning

    When polling multiple motors in MIT mode, make sure their `master_id` values do not conflict. Otherwise, multiple motors may reply with the same CAN ID and the host cannot reliably distinguish the sources.

## 2. MIT Reply Frame Format

The MIT reply frame is always 8 bytes:

| Field | Content |
| --- | --- |
| CAN ID | `master_id` |
| DLC | `8` |
| `data[0]` | Current motor `can_id` |
| `data[1..5]` | Position, velocity, and torque for standard motors. Position, velocity, and force for grippers. |
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

The table lists the encoding ranges for standard motors. Use the device's configured values to decode its feedback. Grippers use mm, mm/s, and N. See the [Gripper Communication Guide](../grippers/communication.md) for their ranges.

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

## 4. AUX Polling Reply Parsing

`mit_aux_enable` controls the last two bytes of the MIT reply:

```text
mit_aux_enable = 0 -> temperature reply: data[6]=NTC1, data[7]=NTC2, both 8-bit encoded
mit_aux_enable = 1 -> AUX polling: data[6..7] carry aux_id + payload
```

Use `mit_aux_enable=1` to enable AUX replies, or `0` to restore temperature replies. Check the [register map matching the device](register_maps/index.md) for the address, data type, and access permissions.

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

Read `aux_id` in each frame and use its decoding rule for `payload` to support both cycle lengths.

## 5. AUX Polling Order and Rate

### 5.1 Older 11-item AUX format

Use this section after confirming that the device supports the 11-item format; it does not apply to every earlier firmware version.

1. Check the [register map matching the device](register_maps/index.md), then set `mit_aux_enable=1` using the address, type, and access permissions specified there. Use `0` for temperature replies instead.
2. Send [MIT control frames](can_communication.md#2-mit-mode-master-control-frame-8-bytes) to the device. A reply is triggered by a received control frame; enabling AUX alone does not start periodic replies. Receive the 8-byte reply on the configured `master_id`.
3. With AUX enabled, decode `data[6..7]` as `aux = (data[6] << 8) | data[7]`, `aux_id = (aux >> 12) & 0x0F`, and `payload = aux & 0x0FFF`. With AUX disabled, these bytes are the two temperature values described in section 8.

Firmware using the 11-item format sends heartbeat `0xF` after `0x9` and then starts the next cycle.

```text
0x0 → 0x1 → 0x2 → 0x3 → 0x4 → 0x5 → 0x6 → 0x7 → 0x8 → 0x9 → 0xF → 0x0
```

Each cycle contains 10 feedback items and one heartbeat. Each item updates at approximately the motor's MIT reply rate divided by 11.

| MIT reply rate | Single item rate |
| ---: | ---: |
| 1000 Hz | 90.9 Hz |
| 500 Hz | 45.5 Hz |
| 100 Hz | 9.1 Hz |

Decode AUX items as described in section 6 and read position from the basic `POS` field in section 3. `0xF` carries a wrapping 12-bit count. The increment between heartbeats depends on the device firmware.

### 5.2 Firmware 1.5.5 (configuration 1.5)

#### Enable and receive replies

1. Set `mit_aux_enable=1` through register `0x6D`, using `type=1` (`bool`) and runtime read/write access. It defaults to `0` at power-on and is not persisted to Flash, so enable it for each run. Writing `0` restores temperature replies. See the [1.5.5 Register Map](register_maps/1.5.5.md).
2. Send [MIT control frames](can_communication.md#2-mit-mode-master-control-frame-8-bytes). A reply is triggered by a received control frame; enabling AUX alone does not start periodic replies. Receive the 8-byte reply on the configured `master_id`.
3. With AUX enabled, decode `data[6..7]` as `aux = (data[6] << 8) | data[7]`, `aux_id = (aux >> 12) & 0x0F`, and `payload = aux & 0x0FFF`. With AUX disabled, these bytes carry NTC1 and NTC2 temperatures as described in section 8.

#### Polling order and heartbeat

`0xA` and `0xB` are sent between `0x9` and heartbeat `0xF`. Each cycle takes 13 replies. Invalid or unsupported items still occupy their slots.

```text
0x0 → 0x1 → 0x2 → 0x3 → 0x4 → 0x5 → 0x6 → 0x7 → 0x8 → 0x9 → 0xA → 0xB → 0xF → 0x0
```

Each item updates at approximately the motor's MIT reply rate divided by 13.

| MIT reply rate | Single item rate |
| ---: | ---: |
| 1000 Hz | 76.9 Hz |
| 500 Hz | 38.5 Hz |
| 100 Hz | 7.7 Hz |

The heartbeat counter advances with each AUX reply and wraps at 12 bits. During continuous polling, compute the difference between two heartbeats from the same motor as `delta = (current - previous) & 0xFFF`. Successive `0xF` items give a `delta` of 13.

#### Additional position items `0xA` and `0xB`

| `aux_id` | Position source | Range | Validity requirements |
| ---: | --- | --- | --- |
| `0xA` | ENCI position derived from the input encoder | `[-max_pos, max_pos]` rad at the output shaft for standard motors, `0..90` mm of displacement for grippers | Valid ENCI calibration and no encoder errors |
| `0xB` | ENCO position measured by the output encoder | `[-max_pos, max_pos]` rad at the output shaft for standard motors | Standard motor with an AC4754 output encoder, valid ENCO calibration, and a successful sample no more than 30 ms old |

Valid position payloads range from `0x000` to `0xFFE`, or `0..4094` in decimal. Position resolution is the range span divided by **4094**. An unmet validity requirement, a non-finite position, or an invalid range returns `0xFFF`. Grippers still send `0xB` with a fixed payload of `0xFFF`.

```text
Standard motors 0xA / 0xB  position_rad = payload × (2 × max_pos) / 4094 − max_pos
Grippers 0xA              position_mm  = payload × 90 / 4094
```

If the final two bytes are `A7 FF`, then `aux_id=0xA` and `payload=0x7FF=2047`. This decodes to `0 rad` for a standard motor or `45 mm` for a gripper.

#### States, validity, and configuration

- `0x2` returns `0xFFF` when the winding temperature observer is disabled or has yet to initialize. `0x9` is the ratio of the reference voltage magnitude to the available voltage `v_bus / √3`. It returns `0xFFF` when the available voltage is at most `0.1 V`.
- `0x7` uses the layout in section 7. Bits 0–3 can also return decimal `11` (`BACKLASH`), `12` (`AGING`), or `13` (`FACTORY`), depending on the device and firmware. Gripper firmware reports bit 6 as 0. On standard motors, use the `0xB` payload to determine whether ENCO position is valid.
- On standard motors, `TOR` carries q-axis current in A in current test mode. During backlash testing, the three basic fields carry the single-turn ENCI position, single-turn ENCO position, and their position difference, all in rad.
- A write to the `can_id` register leaves `master_id` at its current value. Receive replies on the actual configured `master_id`; see the [1.5.5 Register Map](register_maps/1.5.5.md).

## 6. AUX Data Parsing

Both formats use the 11 items below. See section 5.2 for `0xA` and `0xB`.

| `aux_id` | Data | `payload` parsing | Communication range | Resolution |
| ---: | --- | --- | --- | --- |
| `0x0` | NTC1 temperature | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 °C | 0.1 °C |
| `0x1` | NTC2 temperature | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 °C | 0.1 °C |
| `0x2` | Estimated winding temperature | `temp_C = payload / 10.0 - 30.0` | -30.0..150.0 °C | 0.1 °C |
| `0x3` | Bus voltage `v_bus` | `v_bus = payload / 10.0` | 0.0..100.0 V | 0.1 V |
| `0x4` | Estimated bus current | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x5` | Filtered q-axis current | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x6` | Filtered d-axis current | `current_A = payload / 10.0 - 150.0` | -150.0..150.0 A | 0.1 A |
| `0x7` | Program state and runtime flags | See section 7 for bit definitions | `0x000..0xFFF` | bit field |
| `0x8` | Thermal derating coefficient | `coeff = payload / 1000.0` | 0.000..1.000 | 0.001 |
| `0x9` | Voltage utilization | `util = payload / 1000.0` | 0.000..2.000 | 0.001 |
| `0xF` | Heartbeat counter | `heartbeat = payload` | 0..4095, wraps | 1 |

For numeric measurements and coefficients, `payload=0xFFF` indicates invalid or unavailable data. Decode status word `0x7` as a bit field. For heartbeat `0xF`, `0xFFF` is a valid count. Values outside the encoding ranges in the table are clipped to the nearest endpoint.

### Conversion Examples

Use the valid `payload` as an unsigned integer in the matching formula. Physical values are calculated in decimal.

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

`bit6` indicates ENCO calibration status. The list below shows the decimal `FSM state` values shared by both formats. See section 5.2 for the 1.5.5 test states.

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
