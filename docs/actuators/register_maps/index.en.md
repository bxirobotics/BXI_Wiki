---
seo_title: "BXI Motor Register Maps by Firmware Version"
description: "Select a BXI motor register map by software major and minor version. Covers addresses, data types, and access rules for 1.5.x, 1.4.x, 0.3.x, and 0.2.x."
title: Register Maps
---

# Register Maps

Select a register map by the software major and minor version. All patch releases in the same series share a map. For example, `0.3.1` and `0.3.7` both match `0.3.x`. The device configuration version should match the software series and can be read from register `0x7C`.

| Software Series | Configuration Version | Register Map |
| --- | --- | --- |
| `1.5.x` | `1.5` | [1.5 register map](1.5.md) |
| `1.4.x` | `1.4` | [1.4 register map](1.4.md) |
| `0.3.x` | `0.3` | [0.3 register map](0.3.md) |
| `0.2.x` | `0.2` | [0.2 register map](0.2.md) |
