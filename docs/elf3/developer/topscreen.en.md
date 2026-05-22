---
title: Top Screen Guide
---

# Top Screen Guide

The ELF3 top display is used to show basic robot status information. It can also display cute facial expressions to make the robot feel more lively. For secondary development, the screen supports Bluetooth and Wi-Fi communication for wireless data transmission, and it also supports touch interaction.

## Features

The top display can be used for:

- **Robot expressions**: Display cute facial expressions to make the robot feel more lively.
- **Data display**: Supports Bluetooth and Wi-Fi communication for wireless data transmission.
- **Touch interaction**: The screen supports touch input, allowing custom interactive programs to be developed.

## Hardware Platform

The top display is based on the **Waveshare ESP32-S3-Touch-LCD-2.1** touch display development board, which is suitable for robot status display and simple interaction.

| Item | Description |
|---|---|
| MCU | ESP32-S3R8, Xtensa 32-bit LX7 dual-core processor, up to 240MHz |
| Display | 2.1-inch touch screen, 480 x 480 resolution, 262K colors |
| Memory | 16MB Flash, 8MB PSRAM |
| Wireless | 2.4GHz Wi-Fi, Bluetooth 5 (BLE) |
| Common interfaces | USB Type-C, UART, I2C, Micro SD card slot |
| Onboard resources | QMI8658 six-axis sensor, RTC, and more |

!!! note "Interface Note"
    Before hardware debugging, refer to the official Waveshare manual for interface usage restrictions. This helps avoid firmware hangs caused by incorrect programs. If the screen firmware hangs and cannot be flashed normally, follow the recovery steps in the official manual to reflash the firmware.

## Usage

On the real robot, the top display is connected to the robot host through a **USB cable**. This USB connection can be used for firmware flashing and debugging.

Basic usage:

1. Make sure the main robot battery power is turned on.
2. Check that the USB connection between the top display and the robot host is secure.
3. If the display lights up normally, the screen is working.

## Communication

The current real-robot setup uses USB wired communication by default, which is suitable for flashing and debugging. The display hardware also supports **Bluetooth 5 (BLE)** and **2.4GHz Wi-Fi**, but the wireless link, communication protocol, and host-side data publisher need to be developed according to project requirements.

| Method | Current Use | Notes |
|---|---|---|
| USB | Flashing, debugging, host connection | Recommended as the default development and debugging method |
| Bluetooth 5 (BLE) | Optional wireless communication | Requires custom pairing, data protocol, and display logic |
| 2.4GHz Wi-Fi | Optional wireless communication | Requires custom network connection, data protocol, and recovery logic |

## Secondary Development

The top display program is maintained in the <https://github.com/Luckyt1/bxi_show> repository. When modifying displayed content, page layout, backlight behavior, communication method, or reflashing firmware, use the following workflow:

1. Read the build, flashing, and dependency instructions in the `bxi_show` repository.
2. Configure the development environment according to the framework used by the project, referring to the Waveshare Arduino or ESP-IDF documentation as needed.
3. Connect the display to the development host via USB, then compile, flash, and debug through the serial port.
4. After flashing, verify that data refresh works while the robot is stationary before starting motion debugging.

Common development items include:

- Use the LVGL graphics library to develop facial expressions and animations.
- Adjust the layout of voltage, battery level, temperature, and other displayed fields.
- Add robot status, network status, or debugging status indicators.
- Change brightness, sleep timeout, and wake-up behavior.
- Extend BLE or Wi-Fi data communication.
- Add color, icon, or text warnings for abnormal states.

## Debugging Checklist

| Symptom | Possible Cause | Suggested Action |
|---|---|---|
| Screen does not turn on | Main power is off, the display is not powered, USB connection is loose, or firmware is not running | Check battery power, display power, and USB cable; restart the device if needed |
| Screen turns on but data does not update | Host-side data is not being sent, communication is abnormal, or the display program has failed | Check the host-side program status; restart the screen if needed |
| Flashing fails | USB cable issue, port occupied, driver issue, or abnormal download mode | Try another USB cable or port, close programs using the serial port, and enter the flashing workflow again according to the repository instructions |

## References

- Display hardware manual: <https://docs.waveshare.net/ESP32-S3-Touch-LCD-2.1>
- Top display program: <https://github.com/Luckyt1/bxi_show>
