# BXI Motor PC Tool User Guide

## 1. Software Overview

### Basic Information

- Name: `BXI_Tool`
- Icon: <img src="../../assets/other/logo.png" alt="logo" width="45" style="display:inline; vertical-align:middle;" />
- Version: `v260401`
- Languages: Chinese and English (switch in the top-right corner)
- Download: [Go to Download Page](https://download.bxirobotics.cn/%E7%94%B5%E6%9C%BAAPP)

### Interface Overview (Left Menu)

<div style="display:flex; gap:24px; align-items:flex-start; flex-wrap:wrap;">
  <div style="flex:0 0 38%; min-width:180px;">
    <img src="../assets/joint_module/intro.png" alt="Interface Overview" style="width:100%; height:auto; display:block;" />
  </div>
  <div style="flex:1 1 58%; min-width:220px;">

<table style="width:100%; border-collapse:collapse;">
<tr style="border-bottom:1px solid #ddd;">
<th style="text-align:left; padding:8px; border-right:1px solid #ddd;">Menu</th>
<th style="text-align:left; padding:8px;">Description</th>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">Serial</td>
<td style="padding:8px;">Quickly check motor output messages</td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">Debug</td>
<td style="padding:8px;">Control the motor in MIT mode</td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">Calibration</td>
<td style="padding:8px;">Complete magnetic encoder calibration</td>
</tr>
<tr style="border-bottom:1px solid #ddd;">
<td style="padding:8px; border-right:1px solid #ddd;">Config</td>
<td style="padding:8px;">Modify motor parameters</td>
</tr>
<tr>
<td style="padding:8px; border-right:1px solid #ddd;">Firmware</td>
<td style="padding:8px;">Upgrade motor firmware</td>
</tr>
</table>

  </div>
</div>

---

## 2. Connect Motor via bxi_usb2can

### 2.1 Connect Serial Port

Use a USB-to-Type-C cable to connect the debugger to your computer:

- Type-C side to the debugger
- USB side to the computer

Find the correct COM port:

- Windows: right-click Start icon -> Device Manager
- Expand "Ports (COM & LPT)"
- Find the COM port under "USB Serial Device" (e.g. `COM20`, `COM31`)

![COM Example](../assets/joint_module/com.png)

Open `bxi_tool`, then select the corresponding port from the top-left port dropdown. If no port appears, click refresh.

![Connect and Refresh Example](../assets/joint_module/connectrefreash.png)

### 2.2 Select Target

![Connection Example](../assets/joint_module/connect.png)

When the debugger is connected for the first time, it outputs a target selection menu:

- Input `1~8`: communicate with the motor whose `can_id` matches that number
- Input `9`: receive output from all motors on the CAN bus, and use the latest received `can_id` as output ID

Example: choose `9`.

![Selection Example](../assets/joint_module/9.png)

### 2.3 Connect Motor

Connect the motor and debugger through the 2+2 interface:

- Thicker wire: power line
- Thinner wire: signal line (red = H, black = L)

Recommended power input:

- Voltage: `24~48V`
- Current: `3~5A`

After power-on, observe motor serial output.

![Motor Power-on Output Example](../assets/joint_module/boot.png)

---

## 3. Serial Page

Used to view motor output and basic communication information.

![Serial Page](../assets/joint_module/serial.png)

---

## 4. Debug Page

Used for MIT control debugging, command sending, and status monitoring.

![Debug Page](../assets/joint_module/debug.png)

---

## 5. Config Page

Used to modify motor parameters and communication settings.

![Config Page](../assets/joint_module/config.png)

After connecting and powering on the motor, enter the left menu `Config` page to edit parameters.

### 5.1 CAN BUS Settings

Scroll down to the **CAN BUS** section to modify CAN communication parameters.

Key parameters:

- `can_id`: motor ID (the motor receives control frames sent to this ID)
- `master_id`: target sender ID (the motor sends feedback to this ID)

Common operations:

- Read ID: up arrow
- Write ID: down arrow

Rules:

- Writing `can_id` will also update `master_id = can_id | 0x010`
- `master_id` can also be written independently
- If you want to change only `can_id` while keeping a specific `master_id`, write `master_id` again after updating `can_id`

![CAN BUS Section](../assets/joint_module/canbus.png)

### 5.2 Save Parameters

To keep parameters after power-off, use the "Save Parameters" button at the bottom-right after modification.

![Save Parameters Button](../assets/joint_module/configsave.png)

---

## 6. Calibration Page

Used to run the magnetic encoder calibration process.

![Calibration Page](../assets/joint_module/calibration.png)

---

## 7. Firmware Page

Used to upgrade motor firmware.

![Firmware Page](../assets/joint_module/firmware.png)
