# Motor Register Communication Protocol

This page describes how to read, write, save, and query BXI motor configuration registers over CAN. Register maps differ between motor firmware versions, so check the motor software version, hardware/program model, and configuration version before operating on registers.

Unless otherwise noted, CAN IDs, register addresses, data bytes, and example values in this page are hexadecimal. Other bases are called out explicitly.

## 1. Check the Version First

After power-on, the motor outputs boot information. It can be viewed with `bxi_tool`; common fields are:

```text
========== BOOT INFO ==========
STATE : 00 STARTUP
BUILD : Aug 31 2026 10:00:00
VER   : code=1.4.1 config=1.4
CAN   : id=1(boot)

---------- DEVICE CHECK ----------
HW    : Bxi_motor_85
PRO   : NORMAL
CON   : same
```

| Field | Meaning |
| --- | --- |
| `VER code` | Motor software program version. |
| `VER config` | Motor configuration content version, also the register-map version. It can also be read over CAN from `0x7C`. It must match the software version. |
| `CAN id` | Current motor node ID. Use this value as `node_id` in later CAN commands. The boot ID is used by default; the ID source can be changed through registers. |
| `HW` | Motor hardware identification result. |
| `PRO` | Current build target/program model. |
| `CON` | Whether the configuration version matches the program version. |

!!! note

    The first two components of the software version must match the configuration version. For example, software version `1.4.1` corresponds to configuration version `1.4`, and software version `0.3.1` corresponds to configuration version `0.3`. The CAN register interface currently exposes `config_version`, not the full `code=x.y.z` software version. Check the complete software version from the boot information, firmware file name, or upgrade package.

## 2. CAN Command Format

Register commands use the high bits of the standard CAN ID for the command, and the low 4 bits for the motor node:

```text
CAN ID = (cmd << 4) | node_id
```

For example, when the motor `can_id = 1`, the register read command `REG_READ` has `cmd = 0x17`, where `0x17` is hexadecimal. The transmit CAN ID is:

```text
(0x17 << 4) | 0x01 = 0x171
```

| Command | `cmd` | CAN ID when `node_id=1` | DLC | Purpose |
| --- | ---: | ---: | ---: | --- |
| `REG_READ` | `0x17` | `0x171` | 4 | Read one register |
| `REG_WRITE` | `0x18` | `0x181` | 8 | Write one RAM register |
| `REG_SAVE` | `0x19` | `0x191` | 0 | Save RAM configuration to Flash |
| `REG_INFO` | `0x1A` | `0x1A1` | 0 | Query the number of public registers |

## 3. Read Sending and Parsing

Use `REG_READ` to read a register; `cmd = 0x17`.

### 3.1 Transmit Frame

| Field | Content |
| --- | --- |
| CAN ID | `0x17` is the hexadecimal command value. Shift it left by 4 bits, then merge the motor `node_id` into the low 4 bits |
| DLC | `4` |
| `data[0..3]` | `address`, the register address, sent as a 32-bit little-endian value. See the final "Little-Endian Parsing Notes" section. Addresses are normally written in hexadecimal |

The CAN ID has two parts:

```text
High bits: cmd << 4, where cmd is the hexadecimal command value
Low bits : node_id, the current motor CAN id; node_id occupies the low 4 bits
Final CAN ID: (cmd << 4) | node_id
```

For a read command, `cmd` is fixed to hexadecimal `0x17`, so first calculate the command high bits:

```text
0x17 << 4 = 0x170
```

Then merge the motor node ID into the low 4 bits. The calculations below are hexadecimal bitwise OR operations:

| Motor `node_id` | Hex node value | Calculation | Transmit CAN ID |
| ---: | ---: | --- | ---: |
| `1` | `0x01` | `0x170` bitwise OR `0x01` | `0x171` |
| `3` | `0x03` | `0x170` bitwise OR `0x03` | `0x173` |
| `8` | `0x08` | `0x170` bitwise OR `0x08` | `0x178` |

If the motor node is not 1, replace the low 4 bits of the CAN ID. For example, when `node_id=3`, the read command CAN ID is `0x173`.

### 3.2 Reply Parsing

The motor replies with the same CAN ID and an 8-byte payload:

```text
data[0..3] = status | (value_type << 8)
data[4..7] = value_raw
```

All multi-byte fields are little-endian. See the final "Little-Endian Parsing Notes" section.

| Field | Parsing |
| --- | --- |
| `status` | `data[0]`; `0` means success. |
| `value_type` | `(data[1] & 0x07)`, the data type of `value_raw`. |
| `value_raw` | `data[4..7]`, parsed according to `value_type`. |

`status` values:

| `status` | Meaning |
| ---: | --- |
| `0` | OK |
| `1` | Invalid address, or non-zero reserved request header bits |
| `2` | Read-only, or writing is not allowed in the current state |
| `3` | Save failed |
| `4` | DLC too short |
| `5` | Write type mismatch |

`value_type` values:

| `value_type` | Parsing |
| ---: | --- |
| `0` | `int32_t`, little-endian signed integer. See the final "Little-Endian Parsing Notes" section |
| `1` | `bool`, `0=false`, non-zero means `true` |
| `2` | `float`, IEEE754 single-precision floating-point value |
| `3` | `uint32_t`, little-endian unsigned integer. See the final "Little-Endian Parsing Notes" section |
| `4` | `version`, first read as `uint32_t`, then parse with `major=(value>>8)&0xFF`, `minor=value&0xFF` |

### 3.3 Parsing Example

After reading `0x7C`, if the reply is:

```text
171#0004000004010000
```

Split it into bytes:

```text
data[0..3] = 00 04 00 00
data[4..7] = 04 01 00 00
```

Parsing result:

| Item | Result |
| --- | --- |
| `status` | `0x00`, success |
| `value_type` | `0x04`, version |
| `value_raw` | `0x00000104` |
| Configuration version | `major=1`, `minor=4`, so `1.4` |

After reading `0x60`, if the reply is:

```text
171#0000000001000000
```

`value_type=0` means `int32_t`, and `value_raw=0x00000001`, so the current `can_id = 1`.

## 4. Write Sending and Parsing

Use `REG_WRITE` to write a register; `cmd = 0x18`. Writing only changes the configuration value in RAM. To keep the value after power-off, send `REG_SAVE` afterwards.

### 4.1 Transmit Frame

| Field | Content |
| --- | --- |
| CAN ID | `0x18` is the hexadecimal command value. Shift it left by 4 bits, then merge the motor `node_id` into the low 4 bits |
| DLC | `8` |
| `data[0..3]` | `address` bitwise OR `value_type << 8`, little-endian. See the final "Little-Endian Parsing Notes" section |
| `data[4..7]` | `value_raw`, encoded according to the target register type, little-endian. See the final "Little-Endian Parsing Notes" section |

The `value_type` in the write request must match the target register type. For `bool`, write `0` to disable and non-zero to enable; `float` uses IEEE754 single precision.

### 4.2 Reply Parsing

Both successful and failed writes return an 8-byte reply:

```text
data[0..3] = status | (value_type << 8)
data[4..7] = value_raw
```

`status=0` means the write succeeded. The reply `value_type` is the actual type of the target register, and `value_raw` is the current value after the write. `status=5` means the request `value_type` does not match the register type. `status=2` means the register is read-only, or the current motor state does not allow writing.

## 5. Save Sending and Parsing

Use `REG_SAVE` to save configuration; `cmd = 0x19`. It writes the current RAM configuration to Flash.

### 5.1 Transmit Frame

| Field | Content |
| --- | --- |
| CAN ID | `0x19` is the hexadecimal command value. Shift it left by 4 bits, then merge the motor `node_id` into the low 4 bits |
| DLC | `0` |
| Data | Empty |

### 5.2 Reply Parsing

The reply length is 8 bytes:

```text
data[0..3] = status | (3 << 8)
data[4..7] = register_count
```

`status=0` means save succeeded, and `status=3` means save failed. `data[4..7]` is the number of public registers, parsed as little-endian `uint32_t`. See the final "Little-Endian Parsing Notes" section.

## 6. Info Query Sending and Parsing

Use `REG_INFO` to query the number of registers; `cmd = 0x1A`. When host software needs to support different firmware versions, query `REG_INFO` first, then use the `0x7C` configuration version to select the matching register map.

### 6.1 Transmit Frame

| Field | Content |
| --- | --- |
| CAN ID | `0x1A` is the hexadecimal command value. Shift it left by 4 bits, then merge the motor `node_id` into the low 4 bits |
| DLC | `0` |
| Data | Empty |

### 6.2 Reply Parsing

The reply length is 8 bytes:

```text
data[0..3] = status | (3 << 8)
data[4..7] = (writable_count << 16) | register_count
```

Here `value_type=3`, so `value_raw` is parsed as `uint32_t`. For example, `value_raw = 0x00280036` means the number of public registers is `0x0036 = 54`, and the number of writable registers is `0x0028 = 40`.

## 7. Version Differences and Register Map Selection

This page only describes how to send and parse register commands. It does not include the concrete register map. Register maps are provided separately for different program versions. Before using a register address, first confirm the current motor configuration version, then find the matching register map.

Recommended lookup flow:

1. Read `VER code` and `VER config` from the boot information.
2. You can also read `0x7C` over CAN to confirm the current `config_version`.
3. Use the register map matching `VER config`. For example, software version `1.4.1` uses the [1.4.1 register map](register_maps/1.4.1.md), and software version `0.3.1` uses the [0.3.1 register map](register_maps/0.3.1.md).
4. For automatic host-side adaptation, send `REG_INFO` to query the number of public registers, then combine it with the `0x7C` configuration version to select the matching register map.

!!! warning

    Register maps may change between program versions. Host software should not hard-code all parameters only by address. Confirm the configuration version first and use the matching register map.

## 8. Little-Endian Parsing Notes

Little-endian is a byte order for multi-byte data: the low-order byte is placed at the low address, which means the low byte is sent first and the high byte is sent later. In this page, register addresses, `status | (value_type << 8)`, and `value_raw` are all sent and parsed as little-endian values.

For 32-bit data `0x0000007C`, the little-endian byte order is:

```text
7C 00 00 00
```

Therefore, when reading register `0x7C`, `data[0..3]` is:

```text
data[0] = 0x7C
data[1] = 0x00
data[2] = 0x00
data[3] = 0x00
```

For another example, if reply `value_raw` in `data[4..7]` is:

```text
04 01 00 00
```

It is restored to the 32-bit value:

```text
value_raw = 0x00000104
```

If `value_type=4`, the field is a version value and is parsed as:

```text
major = (value_raw >> 8) & 0xFF = 1
minor = value_raw & 0xFF = 4
configuration version = 1.4
```

The final interpretation depends on `value_type`: `int32_t` is parsed as a signed integer, `uint32_t` as an unsigned integer, `float` as an IEEE754 single-precision float, and `version` with the version rule above.
