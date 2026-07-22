---
title: 新版软件后端接口
---

# 新版软件后端接口

本文说明自研 App 如何直接连接并控制 RC ROS2，以及 RC 在局域网和 BLE 上暴露的接口。本地控制方案不依赖账号登录、短信验证或 App 云服务。

!!! warning "安全边界"

    文档中的 UID、SN 和 key 都是示例。机器人云端凭据和服务端密钥不属于 App 控制接口，不得写入 App、源码或日志。

## 1. 接入架构

```mermaid
flowchart LR
    A[自研 App] -->|BLE 首次本地认领| R[RC ROS2]
    A -->|LAN WebSocket / HTTP HMAC| R
    A -->|BLE HMAC8 控制| R
    R -.机器人自身.->|激活 / 心跳 / 日志| C[机器人云服务]
```

- App 可直接控制 RC，不需要账号登录或发送短信验证码。
- App 首次通过 BLE 把本地生成的 UID 和 `deviceKey` 写入机器人。
- 绑定后，App 使用 `deviceKey` 对 WebSocket、HTTP 或 BLE 控制请求签名。
- 机器人仍可独立完成激活、心跳和日志上传；该链路与 App 本地控制相互独立。

## 2. 切换到 BLE 本地认领模式

机器人侧配置：

```text
BXI_BINDING_LOCAL_CLAIM=1
BXI_BINDING_LOCAL_CLAIM_WINDOW_SEC=600
```

修改配置后重启 RC 服务。本地认领窗口从 BLE 服务启动时开始计算；示例为 600 秒。窗口结束后，不再接受新的本地 owner 认领。

本地认领必须同时满足：

- 机器人已激活；
- 机器人当前未绑定 owner；
- `BXI_BINDING_LOCAL_CLAIM=1`；
- 仍在认领时间窗内；
- App 提供的 SN、UID、credential ID 和 32 字节 key 合法。

本地认领默认关闭。启用后，RC 只在设定的时间窗内接受首次认领。认领成功后可将开关恢复为 `0` 并重启服务，已有绑定不会失效。

本地认领写入 `sync_state=local_only`。owner、`deviceKey` 和授权列表只保存在 RC 本地，不参与云端绑定同步；云端绑定状态不会覆盖或删除这些数据。机器人的激活、心跳和日志上传不受影响。

## 3. BLE 首次本地认领

### 3.1 App 生成本地身份

App 使用系统密码学安全随机源生成并持久化：

```text
ownerUid     = [1, 2^63-1] 范围内的随机正整数
ownerKey     = 32 个随机字节
credentialId = 1..128 字符的唯一随机字符串
```

`ownerKey` 就是后续 HMAC 使用的 `deviceKey`。应保存到 Android Keystore、iOS Keychain、Windows Credential Locker 等系统安全存储，不能每次启动重新生成。

### 3.2 Provisioning GATT

UUID 基址：`…-b1a1-4003-8000-000000000000`。

| 服务/特征 | UUID 尾号 | 属性 | 用途 |
|---|---:|---|---|
| Provisioning Service | `00000001` | service | 配网与绑定 |
| PROV_CMD | `00000002` | write | App → RC TLV 帧 |
| PROV_EVT | `00000003` | read/notify | RC → App 响应 |

帧格式：

```text
[version u8=0x03][op u8][seq u8][TLV...]
短 TLV: [tag][len<=0xFE][value]
长 TLV: [tag][0xFF][len u16 little-endian][value]
```

| 请求/响应 | opcode |
|---|---:|
| HELLO / HELLO_ACK | `0x01 / 0x81` |
| WIFI_SCAN / WIFI_LIST | `0x10 / 0x90` |
| WIFI_JOIN / WIFI_STATE | `0x11 / 0x91` |
| BIND_START / BIND_OK / BIND_FAIL | `0x20 / 0xA0 / 0xA1` |
| BIND_CANCEL | `0x21` |
| BIND_STATUS_GET / BIND_STATUS | `0x22 / 0xA2` |
| UNBIND / UNBIND_ACK | `0x23 / 0xA3` |

### 3.3 本地认领请求

App 必须先用 `HELLO` 读取 `HELLO_ACK` 返回的真实 SN，再发送：

```text
BIND_START op=0x20
TLV 0x01 = 省略或空
TLV 0x02 = credentialId UTF-8
TLV 0x03 = HELLO_ACK.sn UTF-8
TLV 0x04 = ownerKey raw bytes，正好 32B
TLV 0x05 = bindMode u8 = 1
TLV 0x06 = ownerUid u64 little-endian
```

成功后，`BIND_OK` 返回 SN、owner UID、credential ID、binding nonce、绑定时间和 key fingerprint，但不会返回 owner key。App 必须校验返回值与本次请求一致后再保存绑定关系。

常见 `BIND_FAIL`：

| 码 | 含义 |
|---:|---|
| 4 | 已被其他 UID 绑定 |
| 5 | 机器人未激活 |
| 6 | 内部错误 |
| 8 | 持久化失败 |

本地模式不能覆盖已有 owner。App 丢失 owner key 后无法从云端恢复，只能使用原 key 授权解绑，或通过设备维护流程清除本地绑定后重新认领。

## 4. 绑定后的 HMAC 鉴权

RC 的控制鉴权只使用 `ownerUid`、机器人 SN 和 32 字节 `deviceKey`，不接受 App access token，也不使用机器人的 `robot_token`。

### 4.1 WebSocket HMAC

```text
message = ws|user_id|sn|ts|nonce
sig = Base64(HMAC-SHA256(deviceKeyRaw, UTF8(message)))
```

连接 query：

```text
user_id=<UID>&client_id=<client-id>&sn=<SN>&ts=<Unix毫秒>&nonce=<随机值>&sig=<URL编码后的Base64签名>
```

```text
ws://<robot>:8081/?user_id=42&client_id=app&sn=BXI-A1&ts=...&nonce=...&sig=...
ws://<robot>:8081/ws/signaling?user_id=42&client_id=video_v1&sn=BXI-A1&ts=...&nonce=...&sig=...
```

时间偏差不得超过 60 秒；每次连接使用新的 nonce。SN 必须与绑定记录一致，UID 必须在授权列表中。

### 4.2 HTTP v2 HMAC

```text
bodyHash = lowercaseHex(SHA256(exactRawBodyBytes))
message = http.v2|UPPER_METHOD|PATH|bodyHash|user_id|sn|ts|nonce
sig = Base64(HMAC-SHA256(deviceKeyRaw, UTF8(message)))
```

请求 query 包含：

```text
auth_v=2&user_id=<UID>&sn=<SN>&ts=<Unix毫秒>&nonce=<随机值>&sig=<URL编码后的Base64签名>
```

`PATH` 不包含 query。空 body 也必须计算 SHA-256。签名必须使用最终实际发送的原始 body 字节，不能在签名后重新格式化 JSON。

### 4.3 BLE 控制 HMAC

协议版本为 `0x03`，所有多字节字段为小端：

```text
22B header: <BBHffffH>
            ver, auth, seq, vx, vy, wz, height, buttons

24B header: <BBHffffHBB>
            基础头 + btn_slot + btn_val

tag = first8Bytes(HMAC-SHA256(deviceKeyRaw, headerBytes))
frame = headerBytes + tag
```

`auth`：`0` 无 tag、`1` HMAC4、`2` HMAC8。生产使用 `auth=2`。每个 BLE 连接维护递增的 u16 `seq`，RC 使用半窗 `0x8000` 处理回绕和防重放。

## 5. RC ROS2 暴露的接口

| 接口 | 地址 | 鉴权 | 用途 |
|---|---|---|---|
| 控制 WebSocket | `ws://<robot>:8081/` | WS HMAC | 控制、遥测、状态 |
| WebRTC signaling | `ws://<robot>:8081/ws/signaling` | WS HMAC | 视频协商 |
| HTTP REST | `http://<robot>:8082` | HTTP v2 HMAC | OTA、地图、导航、建图、巡游 |
| UDP 发现 | UDP `:8083` | 无 | 发现 IP、端口和 SN |
| BLE Provisioning | GATT `…0001` | 近场认领条件 | 配网、绑定、解绑 |
| BLE Control | GATT `…0010` | HMAC8 | 近场遥控 |

### 5.1 UDP 局域网发现

App 向 UDP `:8083` 广播：

```json
{"type":"discover"}
```

RC 每 2 秒广播，并对 discover 单播回复：

```json
{
  "type": "beacon",
  "hostname": "robot_elf3_02",
  "port": 8081,
  "seq": 42,
  "sn": "BXI-EXAMPLE-0001"
}
```

beacon 只用于发现，不能证明设备身份；后续连接仍必须验证 HMAC。

### 5.2 WebSocket 控制

普通消息信封：

```json
{
  "type": "control.cmd_vel",
  "ts": 1780000000000,
  "seq": 1,
  "payload": {}
}
```

App → RC：

| type | 主要 payload | 用途 |
|---|---|---|
| `control.cmd_vel` | `vx,vy,wz,height,mode,btn_1..btn_14` | 遥控；发送者成为当前控制者 |
| `control.heartbeat` | 无 | 保持控制链活跃 |
| `control.authz_set` | `authorized_users[]` | owner 更新授权列表 |
| `control.preflight_abort` | 无 | 取消启动冲突操作 |
| `video.client_stats` | 视频质量字段 | 上报接收质量 |
| `ping` / `health` | `ts?` / 无 | RTT 和健康检查 |
| `system.reboot` / `system.shutdown` | 无 | 特权电源操作 |
| `offer` / `candidate` / `bye` | WebRTC 字段 | signaling |
| `assist.request/cancel/status/extend` | 协助参数 | 远程协助 |
| `logs.list/open/close` | `name/path/tail` | 日志查看 |

速度控制字段必须平铺：

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

没有 `control.acquire` 或 `control.release`。通过鉴权的客户端发送 `control.cmd_vel` 即成为活动控制者；控制连接断开会触发安全停车。客户端应以小于 500ms 的间隔发送控制帧或 heartbeat，默认约 1500ms 没有 ControlIntent 后超时归零。

软急停：

| 动作 | 发送内容 |
|---|---|
| 触发 | `mode:"estop"` 的零速 `control.cmd_vel` |
| 保持 | 每约 200ms 重发 estop 零速帧 |
| 复位 | `mode:"manual" + btn_1:1` 的零速帧 |

RC → App 常用消息：

| type | 用途 |
|---|---|
| `welcome` | 会话和机器人信息 |
| `telemetry.frame` | 电池、位姿、速度、模式、故障 |
| `control.status` | safety、启停和输入限制 |
| `control.manifest` | 动态按钮和状态机定义 |
| `control.state` | 状态机实时状态 |
| `control.authz_ack` | 授权列表更新结果 |
| `pong` / `health` / `error` | 通用响应 |
| `nav.*` | 地图、定位、路径、建图和巡游数据 |
| `offer/answer/candidate/peer_failed/stop` | WebRTC signaling |
| `video.stats` / `video.degraded` | 视频状态 |

### 5.3 HTTP REST（端口 8082）

除 CORS `OPTIONS` 外，以下业务路由均使用 HTTP v2 HMAC：

| 方法 | 路径 | 用途 |
|---|---|---|
| GET | `/api/v1/ota/releases?robot=ELF3` | OTA 目录 |
| GET | `/api/v1/ota/status` | OTA 状态 |
| POST | `/api/v1/ota/start` | `{robot,version,reboot_after,package_names?}` |
| POST | `/api/v1/ota/reboot/precheck` | 重启前检查 |
| POST | `/api/v1/ota/reboot` | `{robot}` 重启 |
| GET | `/api/v1/maps` | 地图列表 |
| GET | `/api/v1/maps/{id}` | 完整地图 |
| GET | `/api/v1/maps/{id}/thumbnail.png` | 缩略图 |
| GET | `/api/v1/maps/{id}/tile/{z}/{x}/{y}.png` | 地图瓦片 |
| GET/PUT | `/api/v1/maps/{id}/{waypoints\|regions\|topology}` | sidecar 读写 |
| POST | `/api/v1/maps/{id}/activate` | 激活定位和导航 |
| POST | `/api/v1/maps/{id}/rename` | `{name}` |
| DELETE | `/api/v1/maps/{id}` | 删除地图 |
| POST | `/api/v1/nav/initial_pose` | `{x,y,yaw,frame_id?,cov?}` |
| POST | `/api/v1/nav/goal` | `{x,y,yaw,frame_id?}` |
| POST | `/api/v1/nav/cancel` | 取消导航 |
| POST | `/api/v1/nav/pause` | `{data:bool}` |
| POST | `/api/v1/tour/start` | `{map_id,waypoint_ids,loop?}` |
| POST | `/api/v1/tour/{pause\|resume\|stop\|skip}` | 巡游控制 |
| GET | `/api/v1/tour/status` | 巡游状态 |
| POST | `/api/v1/mapping/start` | `{base_map_id?}` |
| POST | `/api/v1/mapping/stop` | 停止建图 |
| POST | `/api/v1/mapping/save` | `{name,base_map_id?}` |
| POST | `/api/v1/mapping/pause` | `{data:bool}` |
| POST | `/api/v1/mapping/clear_terrain` | 清除地形 |
| GET | `/api/v1/mapping/status` | 建图状态 |
| PUT | `/api/v1/runtime/mode` | `{mode,map_id?,request_id?}` |
| GET | `/api/v1/runtime/status` | 运行模式和定位质量 |

定位未完成时，App 与 RC 都应拒绝导航和巡游动作。

### 5.4 BLE Control GATT

| 服务/特征 | UUID 尾号 | 属性 | 用途 |
|---|---:|---|---|
| Control Service | `00000010` | service | BLE 控制 |
| CONTROL_CMD | `00000011` | write | HMAC 控制帧 |
| CONTROL_GUEST_AUTH | `00000012` | write | 访客授权证明 |
| CONTROL_STATUS | `00000013` | read/notify | 3B 状态帧 |
| CONTROL_MANIFEST | `00000014` | read/notify | 动态按钮 manifest |
| CONTROL_SM_STATE | `00000015` | read/notify | 状态机状态 |

状态帧：

```text
[ver u8=0x03][flags u8][safety u8]
```

`flags`：`0x01 RUNNING`、`0x02 LOCKED`、`0x04 FAILED`、`0x08 PENDING`、`0x10 UNAUTHORIZED`。

## 6. App 最小控制流程

1. 在机器人侧临时开启本地认领模式并重启 RC 服务。
2. App 生成并安全保存 `ownerUid`、32 字节 `deviceKey` 和 `credentialId`。
3. App 通过 BLE `HELLO_ACK` 读取真实 SN。
4. App 发送本地模式 `BIND_START`，校验 `BIND_OK`。
5. 可关闭本地认领开关并重启，已有绑定不会因此失效。
6. App 通过 UDP beacon、BLE HELLO 或已保存地址找到机器人。
7. App 使用 UID、SN 和 `deviceKey` 生成 WS/HTTP/BLE HMAC。
8. 连接 `:8081` 接收状态并发送 `control.cmd_vel`，按需调用 `:8082`，或直接发送 BLE HMAC8 控制帧。

## 7. 安全要求

- 不得把机器人云端凭据或任何服务端密钥放入 App。
- `deviceKey` 只能保存在 App 系统安全存储和机器人本地，不得写入日志或 analytics。
- 每次 WS/HTTP 请求使用当前时间和新的随机 nonce。
- HTTP 必须对最终实际发送的 body bytes 签名。
- 发布版本必须保持 WS、HTTP 和 BLE HMAC 鉴权开启。
- 本地认领只能认领未绑定机器人，不能用另一 UID 强行覆盖 owner。
- 本地模式没有云端 key 恢复能力；应用应提供安全备份提示和设备重置入口。
