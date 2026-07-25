---
title: New Software Backend Interfaces
---

# New Software Backend Interfaces

This document explains how a custom app can connect to and control RC ROS2 directly, as well as the interfaces exposed by RC over the local network and BLE. Local control does not depend on account login, SMS verification, or an app cloud service.

!!! warning "Security boundary"

    All UIDs, serial numbers, and keys in this document are examples. Robot cloud credentials and server-side keys are not part of the app control interface and must never be embedded in an app, source code, or logs.

## 1. Architecture and binding states

```mermaid
flowchart LR
    A[Custom App] -->|BLE local password binding| R[RC ROS2]
    A -->|LAN WS and HTTP HMAC| R
    A -->|BLE HMAC8 control| R
    M[Maintenance credential] -->|Temporary auth override| R
    R -.->|Activation heartbeat logs| C[Robot Cloud Service]
```

- A custom app can control RC over LAN or BLE without account login, SMS verification, or a BXI App API request.
- The robot still uses the official robot API for activation, heartbeat, and log upload. This cloud connection is independent of local app control.
- Local binding does not require a robot-side environment switch and has no temporary claim window.
- Neither an app access token nor the robot `robot_token` is accepted as an RC control signature.

RC has three persistent binding states:

| State | `binding_mode` | Meaning |
|---|---|---|
| Unbound | `unbound` | Initial cloud or local password binding is allowed |
| Cloud-bound | `cloud` | Bound with a binding credential issued by the official backend |
| Locally bound | `local` | Bound directly between the app and RC with a password, without a cloud user relationship |

Maintenance mode is not a fourth binding state. It is a time-limited authentication override that works while the robot is `unbound`, `cloud`, or `local`. It does not modify the original binding, and RC automatically falls back to the original authentication state when the maintenance credential becomes invalid.

## 2. BLE Provisioning protocol

### 2.1 Provisioning GATT

UUID base: `…-b1a1-4003-8000-000000000000`.

| Service/characteristic | UUID suffix | Properties | Purpose |
|---|---:|---|---|
| Provisioning Service | `00000001` | service | Network provisioning and binding |
| PROV_CMD | `00000002` | write | App → RC TLV frames |
| PROV_EVT | `00000003` | read/notify | RC → App responses |

The legacy connectable BLE advertisement includes the complete Provisioning Service UUID `00000001-b1a1-4003-8000-000000000000`, while the scan response carries the Complete Local Name. The app should filter by this UUID first, then connect, discover GATT, and send `HELLO`. The Control Service UUID is not advertised and must be obtained through GATT service discovery after connecting.

The default advertised name is `BXI_<hostname>`. The hostname is limited to letters, digits, `-`, and `_`, and the name is truncated after 29 UTF-8 bytes. Treat the name as display-only metadata, not device identity; use the serial number returned by `HELLO_ACK` as the authoritative identity.

Frame format:

```text
[version u8=0x03][op u8][seq u8][TLV...]
Short TLV: [tag][len<=0xFE][value]
Long TLV: [tag][0xFF][len u16 little-endian][value]
```

| Request/response | opcode |
|---|---:|
| HELLO / HELLO_ACK | `0x01 / 0x81` |
| WIFI_SCAN / WIFI_LIST | `0x10 / 0x90` |
| WIFI_JOIN / WIFI_STATE | `0x11 / 0x91` |
| BIND_START / BIND_OK / BIND_FAIL | `0x20 / 0xA0 / 0xA1` |
| BIND_CANCEL | `0x21` |
| BIND_STATUS_GET / BIND_STATUS | `0x22 / 0xA2` |
| UNBIND / UNBIND_ACK | `0x23 / 0xA3` |

### 2.2 HELLO_ACK

The app should send `HELLO` first and read the actual serial number and binding state from `HELLO_ACK`:

| TLV | Type | Meaning |
|---:|---|---|
| `0x01` | UTF-8 | Serial number |
| `0x02` | u8 | `bound_flag`: 0 unbound, 1 bound |
| `0x03` | 16B | Device-key fingerprint, right-padded with zeroes |
| `0x04` | UTF-8 | Current IP address |
| `0x05` | UTF-8 | RC firmware version |
| `0x06` | u32 LE | Supported-opcode bitmap |
| `0x07` | u8 | `binding_mode`: 0 unbound, 1 cloud, 2 local |
| `0x08` | bytes | Local-binding KDF salt; empty for other states |
| `0x09` | u32 LE | Local-binding KDF iterations; 0 for other states |
| `0x0A` | u8 | KDF ID; 0 for other states |

`BIND_STATUS_GET` returns `BIND_STATUS` with these fields:

| TLV | Type | Meaning |
|---:|---|---|
| `0x01` | u8 | `bound_flag` |
| `0x02` | UTF-8 | Serial number |
| `0x03` | u64 LE | Owner UID |
| `0x04` | u64 LE | Unix binding time |
| `0x05` | 8B | Device-key fingerprint |
| `0x06` | u8 | `binding_mode`: 0 unbound, 1 cloud, 2 local |
| `0x07` | bytes | KDF salt |
| `0x08` | u32 LE | KDF iterations |
| `0x09` | u8 | KDF ID |

## 3. Local password binding

### 3.1 Fixed identity and password derivation

Local binding uses the fixed owner UID:

```text
ownerUid = 2147483646
```

The password must contain 8 to 64 printable ASCII characters, with every byte in the `0x20..0x7e` range. Derive the 32-byte `deviceKey` as follows:

```text
KDF        = PBKDF2-HMAC-SHA256
password   = UTF-8 password bytes
salt       = 16 cryptographically random bytes
iterations = 200000
dkLen      = 32 bytes
KDF ID     = 1
```

`credentialId` uniquely identifies this local binding and must contain 1 to 128 characters. It contains no secret and may be a UUID or an equivalent unique random string.

Store the derived `deviceKey` in platform secure storage such as Android Keystore, iOS Keychain, or Windows Credential Locker. Never put the password, derived key, or a maintenance credential in logs, analytics, or a plaintext settings file.

### 3.2 BIND_START

The app must first send `HELLO` and read the actual serial number from `HELLO_ACK`, then send:

```text
BIND_START op=0x20
TLV 0x01 = empty; only cloud binding uses a binding credential
TLV 0x02 = credentialId UTF-8
TLV 0x03 = HELLO_ACK.sn UTF-8
TLV 0x04 = deviceKey raw bytes, exactly 32B
TLV 0x05 = bindMode u8 = 1 for a local-binding request
TLV 0x06 = ownerUid u64 LE = 2147483646
TLV 0x07 = KDF salt raw bytes, exactly 16B
TLV 0x08 = iterations u32 LE = 200000
TLV 0x09 = KDF ID u8 = 1
```

RC accepts this request only when the robot has been activated and is currently `unbound`. A local request cannot replace an existing `cloud` or `local` binding, and cloud synchronization does not overwrite a local binding.

On success, RC stores `binding_mode=local`, `sync_state=local_only`, and `bind_method=ble_local_password_v1`. `BIND_OK` returns the serial number, owner UID, credential ID, binding nonce, binding time, and key fingerprint, but never the key. Save the device relationship only after verifying that the response matches the current request.

Common `BIND_FAIL` codes:

| Code | Meaning |
|---:|---|
| 1 | Invalid local fields, UID, key, or KDF parameters |
| 4 | Already bound to another UID |
| 5 | Robot is not activated |
| 6 | Internal error |
| 8 | Persistence failed |

### 3.3 Reconnecting to a locally bound robot

Another app reads the salt, iteration count, and KDF ID from `HELLO_ACK` or `BIND_STATUS`, derives the same `deviceKey` from the user-entered password, and compares the returned fingerprint. It must not save the credential or start control until that check succeeds.

The password and key are never uploaded to the cloud, so local mode has no cloud recovery path. If the password is lost, use a client that still holds the original key to authorize unbinding, or clear the local binding through a controlled maintenance process and bind again.

### 3.4 Unbinding and targeted cloud clearing

When the robot is bound, an owner holding the current `deviceKey` can send an authenticated BLE `UNBIND`:

```text
UNBIND op = 0x23
TLV 0x01  = ts, Unix seconds, u64 little-endian
TLV 0x02  = mac, 16 bytes

payload = "unbind|" || UTF8(sn) || "|" || ts_le_8B
mac = HMAC-SHA256(deviceKeyRaw, payload)[0:16]
```

RC accepts requests within 60 seconds of the robot's current time. While bound, missing TLVs, an out-of-window timestamp, or an invalid HMAC is rejected silently without `UNBIND_ACK`; the sender must handle this as a timeout. The app currently waits five seconds by default. In the unbound/factory state, RC returns `UNBIND_ACK` directly. On success, RC deletes `binding.json` and clears the local sharing-grant records.

- Local-app unbinding does not create, remove, or synchronize any cloud user relationship.
- RC reports `bindingMode` in heartbeat requests and also reports `localBindingCredentialId` while locally bound.
- For an administrator-requested remote clear, RC requires both `binding_mode=local` and an exact match with the current credential ID. A stale command cannot delete a newer replacement binding.

## 4. HMAC authentication after binding

RC control authentication uses a credential UID, robot serial number, and 32-byte key. It does not accept an app access token and does not use the robot's `robot_token`. Normal control uses the owner credential in the binding record; maintenance control uses the temporary credential described in section 6.

### 4.1 WebSocket HMAC

```text
message = ws|user_id|sn|ts|nonce
sig = Base64(HMAC-SHA256(deviceKeyRaw, UTF8(message)))
```

Connection query:

```text
user_id=<UID>&client_id=<client-id>&sn=<SN>&ts=<Unix milliseconds>&nonce=<random value>&sig=<URL-encoded Base64 signature>
```

```text
ws://<robot>:8081/?user_id=42&client_id=app&sn=BXI-A1&ts=...&nonce=...&sig=...
ws://<robot>:8081/ws/signaling?user_id=42&client_id=video_v1&sn=BXI-A1&ts=...&nonce=...&sig=...
```

The timestamp skew must not exceed 60 seconds. Use a new nonce for each connection. The serial number must match the binding record, and the UID must be present in the authorization list.

### 4.2 HTTP v2 HMAC

```text
bodyHash = lowercaseHex(SHA256(exactRawBodyBytes))
message = http.v2|UPPER_METHOD|PATH|bodyHash|user_id|sn|ts|nonce
sig = Base64(HMAC-SHA256(deviceKeyRaw, UTF8(message)))
```

The request query contains:

```text
auth_v=2&user_id=<UID>&sn=<SN>&ts=<Unix milliseconds>&nonce=<random value>&sig=<URL-encoded Base64 signature>
```

`PATH` excludes the query string. The SHA-256 hash must also be calculated for an empty body. Sign the exact final raw body bytes sent on the wire; do not reformat JSON after generating the signature.

### 4.3 BLE control HMAC

The protocol version is `0x03`, and all multibyte fields use little-endian byte order:

```text
22B header: <BBHffffH>
            ver, auth, seq, vx, vy, wz, height, buttons

24B header: <BBHffffHBB>
            base header + btn_slot + btn_val

tag = first8Bytes(HMAC-SHA256(deviceKeyRaw, headerBytes))
frame = headerBytes + tag
```

`auth`: `0` means no tag, `1` means HMAC4, and `2` means HMAC8. Use `auth=2` in production. Maintain an increasing u16 `seq` for each BLE connection. RC uses a `0x8000` half-window for wraparound handling and replay prevention.

## 5. Interfaces exposed by RC ROS2

| Interface | Address | Authentication | Purpose |
|---|---|---|---|
| Control WebSocket | `ws://<robot>:8081/` | WS HMAC | Control, telemetry, and status |
| WebRTC signaling | `ws://<robot>:8081/ws/signaling` | WS HMAC | Video negotiation |
| HTTP REST | `http://<robot>:8082` | HTTP v2 HMAC | OTA, maps, navigation, mapping, and tours |
| UDP discovery | UDP `:8083` | None | Discover IP address, ports, and serial number |
| BLE Provisioning | GATT `…0001` | Proximity and claim conditions | Network provisioning, binding, and unbinding |
| BLE Control | GATT `…0010` | HMAC8 | Proximity control |

### 5.1 UDP local network discovery

The app broadcasts the following payload to UDP `:8083`:

```json
{"type":"discover"}
```

RC broadcasts a beacon every two seconds and sends a unicast reply to discovery requests:

```json
{
  "type": "beacon",
  "hostname": "robot_elf3_02",
  "port": 8081,
  "seq": 42,
  "sn": "BXI-EXAMPLE-0001"
}
```

The beacon is for discovery only and does not prove the device's identity. Subsequent connections must still pass HMAC authentication.

### 5.2 WebSocket control

Standard message envelope:

```json
{
  "type": "control.cmd_vel",
  "ts": 1780000000000,
  "seq": 1,
  "payload": {}
}
```

App → RC:

| type | Main payload | Purpose |
|---|---|---|
| `control.cmd_vel` | `vx,vy,wz,height,mode,btn_1..btn_14` | Remote control; the sender becomes the active controller |
| `control.heartbeat` | None | Keep the control connection active |
| `control.authz_set` | `authorized_users[]` | Owner updates the authorization list |
| `control.preflight_abort` | None | Cancel a conflicting startup operation |
| `video.client_stats` | Video quality fields | Report receive quality |
| `ping` / `health` | `ts?` / None | RTT and health checks |
| `system.reboot` / `system.shutdown` | None | Privileged power operations |
| `offer` / `candidate` / `bye` | WebRTC fields | Signaling |
| `assist.request/cancel/status/extend` | Assistance parameters | Remote assistance |
| `logs.list/open/close` | `name/path/tail` | Log access |

Velocity control fields must be flat members of `payload`:

```json
{
  "type": "control.cmd_vel",
  "payload": {
    "vx": 0.2,
    "vy": 0.0,
    "wz": 0.1,
    "height": 1.0,
    "mode": "manual",
    "btn_1": 0,
    "btn_5": 1
  }
}
```

There is no `control.acquire` or `control.release` message. An authenticated client becomes the active controller when it sends `control.cmd_vel`. Disconnecting the control connection triggers a safe stop. The client should send a control frame or heartbeat at intervals shorter than 500 ms. By default, RC zeros the command after approximately 1500 ms without a ControlIntent.

Soft emergency stop:

| Action | Message |
|---|---|
| Engage | Zero-velocity `control.cmd_vel` with `mode:"estop"` |
| Maintain | Resend the zero-velocity estop frame approximately every 200 ms |
| Reset | Zero-velocity frame with `mode:"manual" + btn_1:1` |

Common RC → App messages:

| type | Purpose |
|---|---|
| `welcome` | Session and robot information |
| `telemetry.frame` | Battery, pose, velocity, mode, and faults |
| `control.status` | Safety, enable state, and input limits |
| `control.manifest` | Dynamic button and state-machine definitions |
| `control.state` | Live state-machine state |
| `control.authz_ack` | Authorization-list update result |
| `pong` / `health` / `error` | General responses |
| `nav.*` | Map, localization, path, mapping, and tour data |
| `offer/answer/candidate/peer_failed/stop` | WebRTC signaling |
| `video.stats` / `video.degraded` | Video status |

### 5.3 HTTP REST (port 8082)

Except for CORS `OPTIONS`, all business routes below use HTTP v2 HMAC:

| Method | Path | Purpose |
|---|---|---|
| GET | `/api/v1/ota/releases?robot=ELF3` | OTA catalog |
| GET | `/api/v1/ota/status` | OTA status |
| POST | `/api/v1/ota/start` | `{robot,version,reboot_after,package_names?}` |
| POST | `/api/v1/ota/reboot/precheck` | Pre-reboot checks |
| POST | `/api/v1/ota/reboot` | Reboot with `{robot}` |
| GET | `/api/v1/maps` | Map list |
| GET | `/api/v1/maps/{id}` | Complete map |
| GET | `/api/v1/maps/{id}/thumbnail.png` | Thumbnail |
| GET | `/api/v1/maps/{id}/tile/{z}/{x}/{y}.png` | Map tile |
| GET/PUT | `/api/v1/maps/{id}/{waypoints\|regions\|topology}` | Read or write sidecar data |
| POST | `/api/v1/maps/{id}/activate` | Activate localization and navigation |
| POST | `/api/v1/maps/{id}/rename` | `{name}` |
| DELETE | `/api/v1/maps/{id}` | Delete a map |
| POST | `/api/v1/nav/initial_pose` | `{x,y,yaw,frame_id?,cov?}` |
| POST | `/api/v1/nav/goal` | `{x,y,yaw,frame_id?}` |
| POST | `/api/v1/nav/cancel` | Cancel navigation |
| POST | `/api/v1/nav/pause` | `{data:bool}` |
| POST | `/api/v1/tour/start` | `{map_id,waypoint_ids,loop?}` |
| POST | `/api/v1/tour/{pause\|resume\|stop\|skip}` | Tour control |
| GET | `/api/v1/tour/status` | Tour status |
| POST | `/api/v1/mapping/start` | `{base_map_id?}` |
| POST | `/api/v1/mapping/stop` | Stop mapping |
| POST | `/api/v1/mapping/save` | `{name,base_map_id?}` |
| POST | `/api/v1/mapping/pause` | `{data:bool}` |
| POST | `/api/v1/mapping/clear_terrain` | Clear terrain |
| GET | `/api/v1/mapping/status` | Mapping status |
| PUT | `/api/v1/runtime/mode` | `{mode,map_id?,request_id?}` |
| GET | `/api/v1/runtime/status` | Runtime mode and localization quality |

The app and RC should both reject navigation and tour actions until localization is complete.

### 5.4 BLE Control GATT

| Service/characteristic | UUID suffix | Properties | Purpose |
|---|---:|---|---|
| Control Service | `00000010` | service | BLE control |
| CONTROL_CMD | `00000011` | write | HMAC control frame |
| CONTROL_GUEST_AUTH | `00000012` | write | Guest authorization proof |
| CONTROL_STATUS | `00000013` | read/notify | 3-byte status frame |
| CONTROL_MANIFEST | `00000014` | read/notify | Dynamic button manifest |
| CONTROL_SM_STATE | `00000015` | read/notify | State-machine state |

Status frame:

```text
[ver u8=0x03][flags u8][safety u8]
```

`flags`: `0x01 RUNNING`, `0x02 LOCKED`, `0x04 FAILED`, `0x08 PENDING`, and `0x10 UNAUTHORIZED`.

## 6. Maintenance mode

Maintenance mode supports factory testing, repair, and on-site service. It works regardless of whether the robot is unbound, cloud-bound, or locally bound. It does not modify `binding.json`, cloud membership, or the original owner. The maintenance credential takes priority only for that maintenance session; after it becomes invalid, the robot continues using its original binding authentication.

### 6.1 Generate a credential on the robot

Use the deployment wrapper from the robot shell:

```bash
sudo /opt/bxi/bxi_rc_ros2/scripts/bxi_maintenance.sh enable
sudo /opt/bxi/bxi_rc_ros2/scripts/bxi_maintenance.sh enable --minutes 120
```

- The default lifetime is 1440 minutes, or 24 hours.
- The allowed range is 30 to 10080 minutes, with a maximum of 7 days.
- The command creates `/var/lib/bxi/maintenance.json` with mode `0600` and prints a text credential beginning with `BXIM1.` only once when it is created.
- When stdout is an interactive terminal and `qrencode` is installed, it also prints a complete ANSI UTF-8 QR code. The text credential is always printed.
- Transfer the complete credential to the app by protected copy or QR code. No account login, SMS verification, or cloud approval is required.

The wrapper uses `/opt/bxi/bxi_rc_ros2` by default. CI or custom installations can override it with `BXI_RC_ROS2_INSTALL_DIR`. If the ROS2/install environment is already sourced, `bxi-maintenance` may also be run directly.

Status does not print the key again:

```bash
sudo /opt/bxi/bxi_rc_ros2/scripts/bxi_maintenance.sh status
```

Revoke it immediately:

```bash
sudo /opt/bxi/bxi_rc_ros2/scripts/bxi_maintenance.sh disable
```

Removing a maintenance code from an app only deletes that app's local copy. It does not revoke the robot-side credential. To revoke early, run `disable` on the robot or generate a new credential to replace the old one.

### 6.2 BXIM1 credential

The credential format is:

```text
BXIM1.<base64url(JSON, without padding)>
```

The decoded JSON contains:

```json
{
  "version": 1,
  "credential_id": "32 lowercase hexadecimal characters",
  "user_id": 2147483645,
  "sn": "BXI-EXAMPLE-0001",
  "key_hex": "64 hexadecimal characters encoding a 32-byte key",
  "created_at": 1780000000,
  "expires_at": 1780007200
}
```

The app must strictly validate the prefix, exact field set, UID, serial number, key length, creation time, and expiry. The credential contains a control key and must be handled like a password: never upload it, log it, or keep it in long-term plaintext storage.

### 6.3 Maintenance authentication

WebSocket and HTTP use the exact HMAC formats in section 4 with the following values from the maintenance credential:

```text
user_id = 2147483645
sn      = token.sn
key     = hexDecode(token.key_hex)
```

For BLE maintenance control, first write UTF-8 JSON to `CONTROL_GUEST_AUTH`. Its signature uses the WS message format:

```json
{
  "maintenance": true,
  "user_id": "2147483645",
  "sn": "BXI-EXAMPLE-0001",
  "ts": "1780000000000",
  "nonce": "a new random value",
  "sig": "Base64 HMAC-SHA256 signature"
}
```

After connection-scoped maintenance authentication succeeds, send the HMAC8 control frames described in section 4.3 using the maintenance key. Existing WS and BLE maintenance sessions are invalidated when the credential expires, is deleted, or is replaced.

### 6.4 Permission boundary

A maintenance credential allows:

- motion control, state, video, and telemetry;
- log access, reboot, and shutdown;
- remote assistance;
- OTA and HTTP management operations;
- maps, navigation, mapping, and tours.

A maintenance credential does not allow:

- `control.authz_set`;
- device sharing or authorization-list changes;
- owner unbinding;
- creating, replacing, or changing a `cloud` or `local` binding.

## 7. Minimum integration flows

Local password binding:

1. Read the actual serial number, binding state, and KDF metadata from BLE `HELLO_ACK`.
2. Only for an `unbound` robot, ask the user to set a local password and generate a 16-byte salt.
3. Derive the key with PBKDF2, send the complete local `BIND_START`, and validate `BIND_OK`.
4. Save the serial number, BLE-device mapping, credential ID, and securely stored key only after binding succeeds.
5. Find the robot through a UDP beacon, BLE HELLO, or a previously saved address.
6. Generate WS, HTTP, or BLE HMAC authentication with the UID, serial number, and key.
7. Connect to `:8081` for state and control; call `:8082` when required, or send BLE HMAC8 control frames.

Maintenance access:

1. Generate a time-limited `BXIM1` credential on the robot.
2. Import and validate it locally in the app without an app-cloud request.
3. Authenticate WS, HTTP, or BLE using the maintenance UID, serial number, and key.
4. Run `sudo /opt/bxi/bxi_rc_ros2/scripts/bxi_maintenance.sh disable` on the robot when service is complete.

## 8. Security requirements

- Never place robot cloud credentials or server-side keys in the app.
- Store the `deviceKey` and maintenance key only in the app's system security storage and in the robot's local storage. Never write either value to logs or analytics.
- Use the current time and a new random nonce for every WS connection and HTTP request.
- For HTTP, sign the exact final body bytes that will be sent.
- Keep WS, HTTP, and BLE HMAC authentication enabled in production builds.
- Local password binding can only bind an unbound robot; it cannot forcibly replace the owner.
- Local mode cannot recover keys from the cloud. The app should provide a secure backup notice and an entry point for device reset.
- Save a BLE-device mapping only after password verification or a successful `BIND_OK`; canceling password setup must not leave a false bound or recoverable-device record.
- Keep `BXIM1` credentials short-lived and revoke them when the task is complete instead of relying only on expiry.
