---
title: Gripper Introduction
---

# Gripper Introduction

The gripper module uses the BXI gripper motor firmware for gripping, opening, closing, and end-effector applications.

## Main Features

- CAN / CAN FD bus communication.
- MIT control mode support.
- MIT control frames use physical position, velocity, and gripper-force values.
- Position is expressed in mm, velocity in mm/s, and feed-forward force in N.
- Runtime status, temperature, and AUX polling feedback are supported.

## Main Parameters

| Parameter | Range or specification | Recommended | Description |
| --- | --- | ---: | --- |
| Position | `0 mm` when closed, approximately `70 mm` when open | — | Actual position depends on the gripper mechanism |
| Protocol encoding range | `0–90 mm` | — | Firmware protocol mapping range |
| Maximum force | 50: approximately `16.37 N`; 50L: approximately `24.03 N` | — | Positive force closes; negative force opens |
| `kp` | `0–5` | `2` | Position stiffness |
| `kd` | `0–1` | `0.05` | Velocity damping |
| MIT control frame | 8 bytes | — | Standard 11-bit CAN ID |

The theoretical feed-forward force range differs between the 50 and 50L grippers. The actual usable gripping force is also affected by the mechanical structure, power supply, and thermal protection. See the [Gripper Communication Guide](communication.md) for detailed communication ranges, frame formats, and register definitions.

## Usage Recommendations

1. Confirm the gripper zero position, opening direction, closing direction, and mechanical limits before first use.
2. Start with `kp=2` and `kd=0.05`.
3. Begin with a low target velocity and small feed-forward force, then tune the parameters based on the actual response.
4. Use `0 mm` for closed and approximately `70 mm` for open; do not treat the protocol upper limit of `90 mm` as the actual opening position.
5. Configure non-conflicting CAN IDs when multiple grippers are used simultaneously.

## Related Documentation

- [Gripper Communication Guide](communication.md)
