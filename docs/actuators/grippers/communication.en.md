---
title: Gripper Communication Guide
---

# Gripper Communication Guide

The communication interface uses standard 11-bit CAN IDs and MIT control frames.

This communication guide applies to all gripper firmware versions in the `0.3.x` and `1.4.x` series.

## 1. Firmware and Parameter Overview

The gripper MIT frame uses physical units rather than the ordinary joint-motor units:

| Field | Ordinary joint motor | Gripper motor |
| --- | --- | --- |
| Position | rad | mm |
| Velocity | rad/s | mm/s |
| `kp` | Configuration dependent | 0–5 |
| `kd` | Configuration dependent | 0–1 |
| `t_ff` / reply torque | N·m | Gripper force in N |

The recommended initial gains are:

```text
kp = 2.00
kd = 0.05
```

## 2. CAN Bus Parameters

The gripper uses the same CAN/CAN FD communication method as the joint module. See the [Joint-Module CAN Communication Guide](../can_communication.md#1-communication-overview) for the common communication overview.

The current gripper communication configuration is a 1 Mbps FDCAN nominal rate, a 5 Mbps data-phase rate, and CAN FD BRS. MIT command and reply frames are 8 bytes long.

| Item | Configuration |
| --- | --- |
| Bus interface | FDCAN / CAN FD |
| Standard ID | 11-bit standard frame ID |
| Nominal rate | 1 Mbps |
| Data-phase rate | 5 Mbps (CAN FD BRS) |
| MIT frame length | 8 bytes |
| Byte order | MIT bit fields use the layout below; register fields are little-endian |

The firmware uses the received frame format for its reply. Keep CAN/CAN FD and BRS settings consistent between the host and the gripper.

## 3. CAN IDs

The general rules for CAN IDs, MIT unicast, broadcast, and reply IDs are the same as for the joint module. See:

- [MIT Mode Master Control Frame](../can_communication.md#2-mit-mode-master-control-frame-8-bytes)
- [CANFD Broadcast Multi-Motor Control](../can_communication.md#3-canfd-broadcast-multi-motor-control)
- [Relationship Between `master_id` and `can_id`](../can_communication.md#53-relationship-between-master_id-and-can_id)

The following only lists the gripper defaults and usage.

### 3.1 MIT Unicast Control

MIT control frames are sent to the gripper `can_id`. The default configuration is:

```text
can_id    = 1
master_id = can_id | 0x010 = 0x011
```

The gripper sends replies to `master_id`, and `data[0]` in the reply contains the gripper's own `can_id`.

| Frame type | CAN ID | Description |
| --- | ---: | --- |
| MIT unicast control | `can_id` | Node 1 uses `0x001` by default |
| MIT broadcast control | `0x7FF` | Carries one 8-byte control block per node |
| MIT reply | `master_id` | Node 1 replies to `0x011` by default |

In a broadcast frame, node `n` uses the 8-byte block at offset `(n - 1) × 8`. The DLC must cover the block for the target node.

### 3.2 Configuration Register CAN IDs

Configuration register commands use:

```text
CAN ID = (cmd << 4) | can_id
```

For the default node `can_id=1`:

| Command | `cmd` | CAN ID | Request DLC |
| --- | ---: | ---: | ---: |
| `REG_READ` | `0x17` | `0x171` | 4 |
| `REG_WRITE` | `0x18` | `0x181` | 8 |
| `REG_SAVE` | `0x19` | `0x191` | 0 |
| `REG_INFO` | `0x1A` | `0x1A1` | 0 |

Configuration-register commands respond only to the target unicast ID. They do not support broadcast register reads or writes.

## 4. MIT Control Frame

The MIT byte layout, bit widths, and packing method are the same as for the joint module. See the [MIT Mode Master Control Frame](../can_communication.md#2-mit-mode-master-control-frame-8-bytes) and [Bit Width Description](../can_communication.md#24-bit-width-description).

The gripper physical ranges and sign convention differ from ordinary joint motors; use the definitions in [Gripper Communication Ranges](#5-gripper-communication-ranges) below.

## 5. Gripper Communication Ranges

### 5.1 Position

The gripper MIT bus position meaning is:

```text
p_des = 0 mm   -> closed
p_des ≈ 70 mm  -> open
```

The recommended physical positions for the current gripper are `0 mm` when closed and approximately `70 mm` when open. The protocol and firmware protection ranges are:

```text
Protocol encoding range: 0–90 mm
Firmware protection range: 0–80.55 mm
```

The firmware clamps the target and feedback position to `0–80.55 mm`, but the host should use the actual approximately `70 mm` open position as the application target. Do not treat `90 mm` as the actual opening position.

Position encoding:

```text
p_raw = uint16((p_des / 90.0) × 65535)
p_des = p_raw / 65535 × 90.0 mm
```

### 5.2 Velocity

The gripper velocity mapping range is calculated from the `max_vel` configuration register:

```text
v_limit = round(89.5 × max_vel / 2π) mm/s
v_des   = -v_limit to +v_limit mm/s
```

The default `max_vel=45 rad/s` corresponds to approximately:

```text
v_des = -642 to +642 mm/s
```

Velocity encoding:

```text
v_raw = uint12((v_des + v_limit) / (2 × v_limit) × 4095)
v_des = v_raw / 4095 × (2 × v_limit) - v_limit
```

### 5.3 `kp` and `kd`

| Parameter | Communication range | Recommended | Description |
| --- | ---: | ---: | --- |
| `kp` | `0–5` | `2` | Position stiffness |
| `kd` | `0–1` | `0.05` | Velocity damping |

```text
kp_raw = uint12(kp / 5.0 × 4095)
kd_raw = uint12(kd / 1.0 × 4095)
```

### 5.4 Feed-forward Force `t_ff`

The MIT `t_ff` field represents gripper force in N. Its range is calculated from the current limit:

```text
F_limit = current_limit × 0.07 × 1 / (2 × 0.007125)
t_ff    = -F_limit to +F_limit N
```

The theoretical default ranges are:

| Build | Default current limit | Theoretical force range |
| --- | ---: | ---: |
| 50 gripper | `10/3 A` | Approximately `-16.37 to +16.37 N` |
| 50L gripper | `14.6667/3 A` | Approximately `-24.03 to +24.03 N` |

Sign convention:

- Positive force/positive torque closes the gripper.
- Negative force/negative torque opens the gripper.
- Maximum force magnitude: approximately `16.37 N` for the 50 gripper and `24.03 N` for the 50L gripper.

The actual usable gripping force is affected by the mechanism, friction, supply voltage, temperature, and current derating.

```text
t_raw = uint12((t_ff + F_limit) / (2 × F_limit) × 4095)
t_ff  = t_raw / 4095 × (2 × F_limit) - F_limit
```

When `t_raw` is `0x7FF` or `0x800`, the firmware decodes it as exactly zero feed-forward force.

## 6. MIT Reply Frame

For the common reply layout and `master_id` rules, see the [Joint-Module Motor Response Frame](../can_communication.md#5-motor-response-frame). The gripper position, velocity, and force fields use the physical ranges in Section 5.

For default NTC decoding, AUX polling format, and polling order of `data[6]` and `data[7]`, see the [MIT Polling Reply Guide](../mit_polling_reply.md). Writing `1` to register `0x6D` switches the last two bytes to AUX polling data.

## 7. Configuration Register Communication

The gripper register configuration function is consistent with the joint-module implementation. For register commands, request and reply formats, save operations, information queries, data types, and write levels, see the [Motor Register Communication Protocol](../register_protocol.md). The sections below only list commonly used registers and gripper-specific parameter ranges.

### 7.1 Request and Reply Format

Register requests use little-endian byte order. `float` values use IEEE754 single-precision format.

```text
REG_READ request:
  data[0..3] = address

REG_WRITE request:
  data[0..3] = address | (value_type << 8)
  data[4..7] = value_raw

Reply:
  data[0..3] = status | (value_type << 8)
  data[4..7] = value_raw
```

| `value_type` | Type |
| ---: | --- |
| `0` | `int32_t` |
| `1` | `bool` |
| `2` | `float` |
| `3` | `uint32_t` |
| `4` | `version` |

### 7.2 Common Gripper Registers

| Address | Parameter | Type | Communication range | Description |
| ---: | --- | --- | --- | --- |
| `0x60` | `can_id` | `int32_t` | Writable in menu/error state | Gripper node ID |
| `0x61` | `master_id` | `int32_t` | Writable in menu/error state | Reply target ID, default `can_id \| 0x010` |
| `0x63` | `can_timeout_ms` | `int32_t` | Runtime read/write | CAN timeout; `0` disables it |
| `0x66` | `mit_mode` | `bool` | Writable in menu/error state | MIT protocol switch |
| `0x67` | `max_pos` | `float` | Runtime read/write | Ordinary motor position parameter; gripper bus range is fixed at `0–90 mm` |
| `0x68` | `max_vel` | `float` | Runtime read/write | Used to calculate gripper velocity range; default `45 rad/s` |
| `0x69` | `max_tor` | `float` | Runtime read/write | Torque limit configuration |
| `0x6A` | `kp_max` | `float` | Runtime read/write | `kp` mapping upper limit; gripper limit is `5` |
| `0x6B` | `kd_max` | `float` | Runtime read/write | `kd` mapping upper limit; gripper limit is `1` |
| `0x6D` | `mit_aux_enable` | `bool` | Runtime read/write | Switches `data[6..7]` to AUX polling |
| `0x7C` | `config_version` | `version` | Read only | Configuration layout version |

### 7.3 Register Write Levels

| Level | Meaning |
| ---: | --- |
| `0` | Runtime read/write |
| `1` | Writable only in menu or error state |
| `2` | System communication parameter; writable only in menu or error state |
| `3` | Read only |

Register writes modify RAM only. To persist a setting across power cycles, confirm `status=0` and then send `REG_SAVE`. `mit_aux_enable` is runtime-only and returns to `0` after power-up, configuration read, or configuration save.

## 8. Communication Examples

For node `1`, write `kd_max=1.0`. The little-endian IEEE754 representation of `float 1.0` is `00 00 80 3F`:

```text
CAN ID: 0x181
DLC:    8
DATA:   6B 02 00 00 00 00 80 3F
```

Read `kd_max`:

```text
CAN ID: 0x171
DLC:    4
DATA:   6B 00 00 00
```

Example MIT command: target position `40 mm`, velocity `0 mm/s`, `kp=2`, `kd=0.05`, and feed-forward force `0 N`:

```text
CAN ID: 0x001
DLC:    8
DATA:   71 C6 7F F6 66 0C C7 FF
```

The example uses `p_raw=0x71C6`, `v_raw=0x7FF`, `kp_raw=0x666`, and `kd_raw=0x0CC`. Zero feed-forward force uses `t_raw=0x7FF`.

## 9. Usage and Safety Notes

1. Read `can_id`, `master_id`, `config_version`, and `kd_max` before first use.
2. Confirm the gripper zero position, direction, and mechanical limits; `0 mm` is closed and approximately `70 mm` is open, while the protocol range `0–90 mm` is not the actual opening position.
3. Start with `kp=2` and `kd=0.05`, using a low target velocity and small `t_ff`.
4. MIT control frames should be sent continuously. If `can_timeout_ms` is non-zero, keep the command period below the timeout.
5. When using broadcast control, reserve the correct 8-byte block for each node and avoid CAN ID conflicts.
6. Change `can_id`, `master_id`, and MIT mode only in the allowed state, confirm the write response, and save the configuration when needed.
