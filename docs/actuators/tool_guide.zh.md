# BXI电机上位机软件使用指南

## 一、软件介绍

### 基本信息

- 名称：`BXI_Tool`
- 图标：<img src="../../assets/other/logo.png" alt="logo" width="45" style="display:inline; vertical-align:middle;" />
- 版本：`v260401`
- 语言：中文与英文（右上角可切换）
- 下载链接：[点击跳转下载站](https://download.bxirobotics.cn/%E7%94%B5%E6%9C%BAAPP)

### 界面介绍（左侧菜单）

<div style="display:flex; gap:24px; align-items:flex-start; flex-wrap:wrap;">
  <div style="flex:0 0 38%; min-width:180px;">
    <img src="../assets/joint_module/intro.png" alt="界面介绍" style="width:100%; height:auto; display:block;" />
  </div>
  <div style="flex:1 1 58%; min-width:220px;">

<table style="width:100%; border-collapse:collapse;">
<tr style="border-bottom:1px solid #ddd;">
<th style="text-align:left; padding:8px; border-right:1px solid #ddd;">菜单项</th>
<th style="text-align:left; padding:8px;">功能说明</th>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">串口终端（Serial）</td>
<td style="padding:8px;">简单查看电机输出</td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">调试界面（Debug）</td>
<td style="padding:8px;">使用 MIT 模式控制电机</td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">电机校准（Calibration）</td>
<td style="padding:8px;">完成磁编校准</td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">参数配置（Config）</td>
<td style="padding:8px;">修改配置参数</td>
</tr>
<tr>
<td style="padding:8px; border-right:1px solid #ddd;">固件烧录（Firmware）</td>
<td style="padding:8px;">升级电机固件</td>
</tr>
</table>

  </div>
</div>

---

## 二、使用 bxi_usb2can 连接电机

### 1）连接串口

通过 USB 转 Type-C 线连接调试器与电脑：

- Type-C 接调试器
- USB 接电脑

查找端口号：

- Windows：右键开始图标 → 设备管理器
- 展开"端口（COM 和 LPT）"
- 查找"USB 串行设备"对应端口（例如 `COM20`、`COM31`）

![COM示意图](../assets/joint_module/com.png)

打开 `bxi_tool` 后，在左上角端口下拉框选择对应端口。若无选项，点击右侧刷新按钮。

![连接刷新示意图](../assets/joint_module/connectrefreash.png)

### 2）选择目标

![接线示意图](../assets/joint_module/connect.png)

首次连接调试器时，会输出目标选择菜单：

- 输入 `1~8`：与 `can_id` 等于对应数字的电机通信
- 输入 `9`：接收 CAN 总线上所有电机输出，并将最后一次接收到的 `can_id` 作为输出 ID

示例：选择 `9`。

![实例示意图](../assets/joint_module/9.png)

### 3）连接电机

电机与调试器通过 2+2 接口连接：

- 较粗线：电源线
- 较细线：信号线（红色对应 H，黑色对应 L）

供电建议：

- 输入电压：`24~48V`
- 输入电流：`3~5A`

上电后观察电机串口输出。

![电机上电输出示例](../assets/joint_module/boot.png)

---

## 三、串口界面（Serial）

用于查看电机输出与基础通信信息。

![串口界面截图](../assets/joint_module/serial.png)

---

## 四、调试界面（Debug）

用于 MIT 控制调试、参数下发与状态观察。

![调试界面截图](../assets/joint_module/debug.png)

---

## 五、配置界面（Config）

用于修改电机参数与通信设置。

![配置界面截图](../assets/joint_module/config.png)

连接上电机后，进入左侧菜单 `Config` 页面可修改参数。

### 5.1 CAN BUS 配置

下翻到 **CAN BUS** 区域可修改 CAN 通信参数。

关键参数：

- `can_id`：电机 ID（电机接收该 ID 的控制帧）
- `master_id`：发送目标 ID（电机向该 ID 回传信息）

常用操作：

- 读取 ID：上箭头
- 写入 ID：下箭头

规则说明：

- 写入 `can_id` 时，会同步写入 `master_id = can_id | 0x010`
- 也支持单独写入 `master_id`
- 如果希望只改 `can_id` 而保留特定 `master_id`，需在改完 `can_id` 后重新写入 `master_id`

![CAN BUS 参数区截图](../assets/joint_module/canbus.png)

### 5.2 参数保存

若希望参数掉电不丢失，请在修改后使用右下角"保存参数"功能。

![保存参数按钮截图](../assets/joint_module/configsave.png)

---

## 六、校准界面（Calibration）

用于执行磁编校准流程。

![校准界面截图](../assets/joint_module/calibration.png)

---

## 七、固件烧录（Firmware）

用于升级电机固件。

![固件烧录界面截图](../assets/joint_module/firmware.png)

