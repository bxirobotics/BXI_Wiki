# CAN Communication Guide

This document describes the CAN/CANFD communication protocol of the BXI joint module in MIT control mode.

## 1. Communication Overview

The motor uses **CANFD** communication and is compatible with classic CAN. The motor replies using the same frame format as the received CANFD/CAN frame, so frame type and variable bitrate usually do not need separate configuration.

- Max CANFD bitrate: `1M + 5M`
- Bitrate without variable bitrate: `1M`

By function, frames are divided into:

- **Master control frame**: control commands sent from upper controller to motor
- **Motor response frame**: motor status feedback sent from motor to upper controller

---

## 2. MIT Mode Master Control Frame (8 Bytes)

### 2.1 Data Layout

| Control Frame | D[0] | D[1] | D[2] | D[3] | D[4] | D[5] | D[6] | D[7] |
|---|---|---|---|---|---|---|---|---|
| ID | `p_des[15:8]` | `p_des[7:0]` | `v_des[11:4]` | `v_des[3:0] \| Kp[11:8]` | `Kp[7:0]` | `Kd[11:4]` | `Kd[3:0] \| t_ff[11:8]` | `t_ff[7:0]` |

### 2.2 Field Description

- **Frame ID**: equals target motor `can_id`, default `1`; broadcast frame uses `0x7FF`
- `p_des`: position command value
- `v_des`: velocity command value
- `Kp`: position proportional gain
- `Kd`: position differential gain
- `t_ff`: torque feedforward value

### 2.3 Default Parameter Ranges

`Kp` / `Kd` ranges (configurable via upper computer):

- `Kp`: `[0, 500]`
- `Kd`:
  - `MOTOR_50`: `[0, 5]`
  - `MOTOR_50_L`: `[0, 5]`
  - `MOTOR_70`: `[0, 5]`
  - `MOTOR_85`: `[0, 20]`
  - `MOTOR_J3505`: `[0, 5]`
  - `MOTOR_J3510`: `[0, 5]`

`p_des` / `v_des` / `t_ff` ranges (configurable via upper computer):

- `p_des`: `[0, 12.5]`
- `v_des`: `[0, 45.0]`
- `t_ff`:
  - `MOTOR_50`: `[0, 40]`
  - `MOTOR_50_L`: `[0, 40]`
  - `MOTOR_70`: `[0, 80]`
  - `MOTOR_85`: `[0, 160]`
  - `MOTOR_J3505`: `[0, 18]`
  - `MOTOR_J3510`: `[0, 18]`

Temperature communication range: `[-30.0, 150.0]` ℃.

### 2.4 Bit Width Description

A standard CAN frame has only 8 bytes. The MIT control command packs 5 parameters into 8 bytes:

- Position: 16 bits (2 bytes)
- Velocity: 12 bits
- Kp: 12 bits
- Kd: 12 bits
- Torque: 12 bits

---

## 3. CANFD Broadcast Multi-Motor Control

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

## 4. Special Control Frames (8 Bytes)

All commands below are fixed 8-byte values:

- Motor enable: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFC`
- Motor disable: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFD`
- Save zero position: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFE`
- Enable terminal output: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFB`
- Disable terminal output: `0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFF 0xFA`

---

## 5. Motor Response Frame

The response frame ID can be configured via upper computer, default `0x11` (internal field: `master_id`).

Main feedback includes position, velocity, torque, driver temperature, and motor temperature.

### 5.1 Data Layout

| Feedback Frame | D[0] | D[1] | D[2] | D[3] | D[4] | D[5] | D[6] | D[7] |
|---|---|---|---|---|---|---|---|---|
| MST_ID | `ID` | `POS[15:8]` | `POS[7:0]` | `VEL[11:4]` | `VEL[3:0] \| T[11:8]` | `T[7:0]` | `T_MOS` | `T_Motor` |

### 5.2 Field Description

- `ID`: motor ID
- `POS`: position data
- `VEL`: velocity data
- `T`: torque data
- `T_MOS`: MOS temperature on driver (℃)
- `T_Motor`: internal winding temperature (℃)

Position, velocity, and torque use linear mapping to convert floating-point values to signed fixed-point values:

- Position: 16 bits
- Velocity: 12 bits
- Torque: 12 bits

### 5.3 Relationship Between `master_id` and `can_id`

- Default relation: `master_id = can_id | 0x010`
- Modifying `can_id` will synchronize update of `master_id`
- `master_id` can also be written independently via upper computer
