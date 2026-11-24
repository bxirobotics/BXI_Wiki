---
seo_title: "BXI Motor CAN/CANFD and MIT Control Frames"
description: "Choose the BXI actuator CAN and CAN FD MIT protocol by firmware version. See earlier control and reply formats and firmware 1.5.5 ranges, registers, and 13-item AUX polling."
---

# CAN Communication Guide

Read the device's software and configuration versions from its startup information. This guide covers the earlier MIT protocol first, followed by software `1.5.5` with configuration `1.5`. Gripper motion fields use their own ranges. See the [Gripper Communication Guide](../grippers/communication.md).

## MIT protocol on other firmware versions

The following sections describe the earlier MIT protocol. Use the register map matching the device software and configuration, such as [0.2](register_maps/0.2.md), [0.3](register_maps/0.3.md), or [1.4](register_maps/1.4.md). Check the device firmware for AUX support and its polling format.

### 1. Communication Overview

The motor supports CAN FD and classic CAN. Replies follow the received frame format. Configure the host bus for the frame type and bitrates supported by the device.

- Max CANFD bitrate: `1M + 5M`
- Bitrate without variable bitrate: `1M`

By function, frames are divided into:

- **Master control frame**: control commands sent from upper controller to motor
- **Motor response frame**: motor status feedback sent from motor to upper controller

---

### 2. MIT Mode Master Control Frame (8 Bytes)

#### 2.1 Data Layout

| Control Frame | D[0] | D[1] | D[2] | D[3] | D[4] | D[5] | D[6] | D[7] |
|---|---|---|---|---|---|---|---|---|
| ID | `p_des[15:8]` | `p_des[7:0]` | `v_des[11:4]` | `v_des[3:0] \| Kp[11:8]` | `Kp[7:0]` | `Kd[11:4]` | `Kd[3:0] \| t_ff[11:8]` | `t_ff[7:0]` |

#### 2.2 Field Description

- **Frame ID**: equals target motor `can_id`, default `1`; broadcast frame uses `0x7FF`
- `p_des`: position command value
- `v_des`: velocity command value
- `Kp`: position proportional gain
- `Kd`: position differential gain
- `t_ff`: torque feedforward value

#### 2.3 Default Parameter Ranges

These are reference ranges from the earlier MIT protocol. Use the current device settings to encode and decode values in rad, rad/s, and Nm. For grippers, use the ranges in the gripper communication guide.

**`Kp` / `Kd` ranges (configurable via upper computer)**

| Parameter | Applicable object | Range |
|---|---|---|
| `Kp` | General | `[0, 500]` |
| `Kd` | `MOTOR_50` | `[0, 5]` |
|  | `MOTOR_50_L` | `[0, 5]` |
|  | `MOTOR_70` | `[0, 5]` |
|  | `MOTOR_85` | `[0, 20]` |
|  | `MOTOR_J3505` | `[0, 5]` |
|  | `MOTOR_J3510` | `[0, 5]` |

**`p_des` / `v_des` / `t_ff` ranges (configurable via upper computer)**

| Parameter | Applicable object | Range |
|---|---|---|
| `p_des` | General | `[-12.5, 12.5]` |
| `v_des` | General | `[-45.0, 45.0]` |
| `t_ff` | `MOTOR_50` | `[-40.0, 40]` |
|  | `MOTOR_50_L` | `[-40, 40]` |
|  | `MOTOR_70` | `[-80, 80]` |
|  | `MOTOR_85` | `[-160, 160]` |
|  | `MOTOR_J3505` | `[-18, 18]` |
|  | `MOTOR_J3510` | `[-18, 18]` |

Temperature communication range: `[-30.0, 150.0]` ℃.

#### 2.4 Bit Width Description

A standard CAN frame has only 8 bytes. The MIT control command packs 5 parameters into 8 bytes:

- Position: 16 bits (2 bytes)
- Velocity: 12 bits
- Kp: 12 bits
- Kd: 12 bits
- Torque: 12 bits

---

### 3. CANFD Broadcast Multi-Motor Control

A CANFD frame can carry up to 64 bytes. In multi-motor control:

- Frame ID is fixed to `0x7FF`
- Data for motor `id` occupies its 8-byte block: `(id - 1) * 8` to `id * 8 - 1`

That is, each motor uses a full 8-byte MIT control block, concatenated in motor-ID order in one frame.

Example (first 16 bytes, controlling M[1] and M[2]):

| Control Frame (ID=0x7FF) | D[0] | D[1] | D[2] | D[3] | D[4] | D[5] | D[6] | D[7] |
|---|---|---|---|---|---|---|---|---|
| M[1] | `p_des[15:8]` | `p_des[7:0]` | `v_des[11:4]` | `v_des[3:0] \| Kp[11:8]` | `Kp[7:0]` | `Kd[11:4]` | `Kd[3:0] \| t_ff[11:8]` | `t_ff[7:0]` |

| Control Frame (ID=0x7FF) | D[8] | D[9] | D[10] | D[11] | D[12] | D[13] | D[14] | D[15] |
|---|---|---|---|---|---|---|---|---|
| M[2] | `p_des[15:8]` | `p_des[7:0]` | `v_des[11:4]` | `v_des[3:0] \| Kp[11:8]` | `Kp[7:0]` | `Kd[11:4]` | `Kd[3:0] \| t_ff[11:8]` | `t_ff[7:0]` |

Subsequent motors follow in 8-byte steps.

> For example, motor 3 uses D[16]~D[23], motor 4 uses D[24]~D[31], and so on, up to 64 bytes.

---

### 4. Special Control Frames (8 Bytes)

All commands below are fixed 8-byte values:

- Motor enable: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFC`
- Motor disable: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFD`
- Save zero position: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFE`
- Enable terminal output: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFB`
- Disable terminal output: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFA`

---

### 5. Motor Response Frame

The motor sends an 8-byte reply when it receives a valid MIT control block. Receive the reply on the device's configured `master_id`. For example, node `1` defaults to reply ID `0x11`.

The table below shows the earlier temperature reply layout. On earlier firmware that supports AUX, configure `mit_aux_enable` using the matching register map. With AUX off, the last two bytes are 8-bit temperatures. Convert each with `raw × 180 / 255 − 30` in °C.

When AUX is enabled on devices using 11-item polling, combine `data[6]` and `data[7]` into a 16-bit field with the high byte first. The upper four bits are `aux_id`, and the lower 12 bits are `payload`. The cycle is `0x0..0x9 → 0xF`, and each item updates at the MIT reply rate divided by 11. Read position from the basic `POS` field. See [section 5.1 of the MIT Polling Reply Guide](mit_polling_reply.md#51-older-11-item-aux-format).

#### 5.1 Data Layout

| Feedback Frame | D[0] | D[1] | D[2] | D[3] | D[4] | D[5] | D[6] | D[7] |
|---|---|---|---|---|---|---|---|---|
| MST_ID | `ID` | `POS[15:8]` | `POS[7:0]` | `VEL[11:4]` | `VEL[3:0] \| T[11:8]` | `T[7:0]` | `T_MOS` | `T_Motor` |

#### 5.2 Field Description

- `ID`: motor ID
- `POS`: position data
- `VEL`: velocity data
- `T`: torque data
- `T_MOS`: MOS temperature on driver (℃)
- `T_Motor`: motor temperature sensor reading (°C)

Position, velocity, and torque are unsigned codes mapped linearly to the configured ranges.

- Position: 16 bits
- Velocity: 12 bits
- Torque: 12 bits

#### 5.3 Relationship Between `master_id` and `can_id`

- Default relation: `master_id = can_id | 0x010`
- After changing the node address, check the active `can_id` and `master_id` on the device
- Where supported, configure `master_id` separately using the matching register map

## MIT protocol on firmware 1.5.5 (configuration 1.5)

### Bus settings and control frames

1. Use standard 11-bit CAN IDs. Use 1 Mbps for classic CAN or CAN FD without BRS. With BRS enabled, the CAN FD nominal rate is 1 Mbps and the data rate is 5 Mbps. MIT replies follow the request's CAN frame type and BRS setting.
2. Set the device to MIT communication mode. Send a unicast frame to its `can_id`. Each control block is eight bytes, with 16 bits for position and 12 bits for each remaining field. See [section 2](#2-mit-mode-master-control-frame-8-bytes) for the byte layout.
3. For multi-motor broadcast, use CAN FD ID `0x7FF` and position blocks by node ID. The block for node `n` starts at byte `(n - 1) × 8`. The frame must include the node's complete eight-byte block. A 64-byte frame fits the blocks for nodes 1 through 8.

Use the device's current encoding ranges for commands and feedback. See the [1.5 Register Map](register_maps/1.5.md) for addresses and access permissions.

| Control field | Bits | Standard motor encoding range | Range register |
| --- | ---: | --- | --- |
| Position `p_des` | 16 | `[-max_pos, max_pos]` rad | `0x67` |
| Velocity `v_des` | 12 | `[-max_vel, max_vel]` rad/s | `0x68` |
| Feedforward torque `t_ff` | 12 | `[-max_tor, max_tor]` Nm | `0x69` |
| Position gain `Kp` | 12 | `[0, kp_max]` | `0x6A` |
| Velocity gain `Kd` | 12 | `[0, kd_max]` | `0x6B` |

For example, the 95 2.0 variant has factory encoding maxima of `kp_max=800`, `kd_max=50`, and `max_tor=360 Nm`. Decode using the device's current configuration. The encoding range and operating torque limit `torquet_limit` are configured separately.

Signed physical values map to unsigned codes. For the 12-bit feedforward torque command, both `0x7FF` and `0x800` decode to `0 Nm`.

### Special control frames and reply ID

The special frames in section 4 still use seven `FF` bytes followed by one command byte. `FC` requests enable and `FD` requests a return to the menu. `FE` sets and saves zero. `FB` and `FA` enable and disable CAN terminal log forwarding, respectively. The last three commands require menu state. The reply to a special frame reports the state before the command is processed.

MIT replies use the current `master_id`. A direct write to the `can_id` register leaves `master_id` at its current value. If startup synchronization with the Bootloader ID is enabled, startup sets the reply ID from the synchronized node address.

### Temperature replies and 13-item AUX polling

Each valid MIT control frame triggers one 8-byte status reply. Both modes carry `can_id` in `data[0]` and basic feedback in `data[1..5]`. Standard motors report position, velocity, and torque. Grippers report displacement, velocity, and force.

| `mit_aux_enable` | `data[6]` | `data[7]` | Decoding |
| --- | --- | --- | --- |
| `0` (power-on default) | NTC1 | NTC2 | 8 bits each, temperature in °C is `raw × 180 / 255 − 30` |
| `1` | AUX high byte | AUX low byte | Upper 4 bits are `aux_id`, lower 12 bits are `payload` |

Write `1` to register `0x6D` (`type=1`, `bool`) during operation to enable AUX. Enable it again after power-on. Register replies use the request's CAN ID, and subsequent MIT status replies use `master_id`. See the [Motor Register Communication Protocol](register_protocol.md) for write and reply formats.

AUX cycles through `0x0..0x9 → 0xA → 0xB → 0xF` in 13 replies. Each item updates at the MIT reply rate divided by 13. `0xA` carries ENCI position and `0xB` carries ENCO position. Valid position payloads are `0x000..0xFFE` with **4094** as the scaling denominator. `0xFFF` indicates an invalid position. See [section 5.2 of the MIT Polling Reply Guide](mit_polling_reply.md#52-firmware-155-configuration-15) for ranges, validity conditions, and heartbeat decoding.
