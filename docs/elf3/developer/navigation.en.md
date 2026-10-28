---
seo_title: "ELF3 Navigation App: LiDAR, Mapping and Tours"
description: "Configure ELF3 navigation with Livox MID-360s LiDAR and the BXI RC App, from network and ROS2 setup to mapping, map editing and guided-route operation on the robot."
---

# ELF3 Navigation App User Guide

This guide explains how to configure a Livox MID-360s LiDAR for ELF3 and use `bxi_rc_app` to create maps, edit navigation data, and run guided tours.

Reference project: [bxi_nav](https://github.com/Luckyt1/bxi_nav)

## Prerequisites

- Install the latest version of `bxi_rc_app`.
- Prepare an ELF3 robot equipped with a Livox MID-360s LiDAR.
- Make sure both `bxi_rc_slam` and `bxi_rc_ros2` are up to date. Update `bxi_rc_ros2` first to ensure the environment is complete.
- Connect the computer directly to the LiDAR with an Ethernet cable.
- Keep the operating area safe and the paths clear.

## 1. Configure the Livox MID-360s LiDAR

If the LiDAR does not start, the network or device configuration is usually incorrect. First confirm that the computer and LiDAR are on the same subnet, then check the LiDAR network settings in the app.

### 1.1 Configure a Static IP Address

Set the computer's Ethernet interface to a static IP address, such as `192.168.1.51`. A direct Ethernet connection is recommended. Changing network settings through a remote desktop session may cause permission issues.

![Open the computer's network settings](../../assets/elf3/developer/navigation/network-settings.png)

![Configure a static IP address for the Ethernet interface](../../assets/elf3/developer/navigation/static-ip-configuration.png)

### 1.2 Configure the LiDAR in the App

1. Open `bxi_rc_app` and connect to the robot. On the robot details page, select **Map Management (地图管理)**, then **New Map (新建地图)** to open the mapping screen.

    ![Open Map Management from the robot details page](../../assets/elf3/developer/navigation/lidar-config-map-management.jpg)

2. Select the **Settings** icon in the upper-right corner of the mapping screen, circled in red below.

    ![Open Settings in the upper-right corner of the mapping screen](../../assets/elf3/developer/navigation/lidar-config-settings-entry.jpg)

3. Select **LiDAR (雷达)** on the Settings page. Under **Available Network Interface Addresses (可用网卡地址)**, select the robot's network interface connected to the LiDAR to fill in **Robot Receive IP (机器人接收 IP)**.

    The screenshot shows the Ethernet interface `enp86s0` with a receive IP of `192.168.1.52`. Use the actual interface address rather than copying the example, and keep the receive IP distinct from the LiDAR IP.

    ![Select the network interface connected to the LiDAR and fill in the robot receive IP](../../assets/elf3/developer/navigation/lidar-config-receive-ip.jpg)

4. Select **Search for LiDAR (搜索雷达)**, then select the matching device in the results to fill in **LiDAR IP (雷达 IP)**. You can also enter the address manually if you already know the LiDAR's actual IP.

    The MID360S in the screenshot has the IP address `192.168.1.100`. Use the address from your actual search results.

    ![Search for the LiDAR and fill in its IP address](../../assets/elf3/developer/navigation/lidar-config-search-result.jpg)

5. Check that **Robot Receive IP (机器人接收 IP)** and **LiDAR IP (雷达 IP)** are correct, then select **Save Configuration (保存配置)**. Wait for confirmation that the configuration has been saved, then restart the robot.

6. After the restart, reconnect to the robot and return to the mapping screen. Make sure the head-mounted LiDAR points vertically downward and the robot remains stable, then select **Start (开始)** at the top. A red point cloud indicates that LiDAR data is being received correctly and the LiDAR configuration is complete.

    ![A red point cloud after starting mapping confirms that LiDAR data is being received](../../assets/elf3/developer/navigation/lidar-config-point-cloud.jpg)

## 2. Use the Navigation App

!!! warning "Check the head-mounted LiDAR orientation"

    Before entering the mapping or navigation screen, ensure that the robot's head-mounted LiDAR is **pointing vertically downward**.

1. Open `bxi_rc_app` and select **My Devices (我的设备)**.

   ![Open My Devices in bxi_rc_app](../../assets/elf3/developer/navigation/open-my-devices.jpg)

2. Select the robot you want to navigate from the device list to open its details page.

   ![Select the robot from My Devices](../../assets/elf3/developer/navigation/select-robot.jpg)

3. Open **Map Management (地图管理)** from the robot details page.

   ![Open Map Management from the robot details page](../../assets/elf3/developer/navigation/open-map-management.jpg)

### 2.1 Create a Map

!!! warning "Keep the robot stable before mapping"

    Position the robot's head upright and keep its body stable. Avoid large movements that could interfere with IMU initialization.

Complete mapping workflow demo:

![type:video](../../assets/elf3/developer/navigation/mapping-workflow-demo.mp4 "Complete mapping workflow demo")

1. Open **Map Management (地图管理)** and select **New Map (新建地图)**.

   ![Create a map from the Map Management page](../../assets/elf3/developer/navigation/create-map.jpg)

2. Start the robot and keep it in walking mode. After confirming that the point cloud is displayed correctly, select **Start Mapping (开始建图)**.

   ![Confirm the point cloud and start mapping](../../assets/elf3/developer/navigation/mapping-in-progress.jpg)

3. During mapping, stand behind the robot and remotely drive it through the target area. Keep pedestrian movement to a minimum to avoid capturing people in the map.

    The new version supports dynamic obstacle filtering. If people or other moving obstacles are captured in the map, wait for them to leave, then remotely drive the robot through the affected area again to rescan it and filter out the remaining traces.

4. After the map covers the target area, select **Save (保存)**. Wait for confirmation that the map has been saved before leaving the mapping page.

   ![Complete mapping and save the map](../../assets/elf3/developer/navigation/mapping-complete.jpg)

   ![type:video](../../assets/elf3/developer/navigation/save-map-demo.mp4 "Save map demo")

### 2.2 Edit the Map

Guided-tour editing demo:

![type:video](../../assets/elf3/developer/navigation/tour-editing-demo.mp4 "Guided-tour editing demo")

1. In **Map Management (地图管理)**, select the map you just saved.

   ![Select the saved map from Map Management](../../assets/elf3/developer/navigation/select-map.jpg)

2. Open the guided-tour editor, switch to **Waypoint (航点)**, and mark each destination on the map.

   ![Add a waypoint to the map](../../assets/elf3/developer/navigation/add-waypoint.jpg)

3. Set the robot's arrival heading for each waypoint. Add a waypoint name if needed.

   ![Set the waypoint name and arrival heading](../../assets/elf3/developer/navigation/set-waypoint-heading.jpg)

4. Optional: To make the robot perform a specific behavior after reaching the waypoint, select **Add Action (添加动作)**, choose **Voice (语音)**, **Action (动作)**, or **Delay (延迟)**, configure it, and then select **Add (添加)**. You can add multiple behaviors to the same waypoint if needed.

   ![Add an arrival action to the waypoint](../../assets/elf3/developer/navigation/waypoint-add-arrival-action.jpg)

   ![Configure a voice, action, or delay after arrival](../../assets/elf3/developer/navigation/waypoint-configure-arrival-action.jpg)

5. Switch to **Area (区域)** and select **Add Clearing Zone (添加清除区)**. Draw clearing zones over the robot's travel paths to remove obstacles that no longer exist in the physical environment.

   ![Add a clearing zone over a travel path](../../assets/elf3/developer/navigation/add-clearing-zone.jpg)

6. Verify the waypoints, headings, arrival behaviors, and clearing zones, then wait for the map to be saved successfully.

### 2.3 Start a Guided Tour

!!! warning "Keep the robot stable before starting the tour"

    Position the robot's head upright and keep its body stable. Avoid large movements that could interfere with IMU initialization.

1. Return to the robot details page, open **Operating Mode (运行模式)**, and select guided-tour mode.

   ![Open the robot's Operating Mode menu](../../assets/elf3/developer/navigation/open-operation-mode.jpg)

2. Select the required map, then select **Start (开始)** on its card.

   ![Select a map and start the guided tour](../../assets/elf3/developer/navigation/select-navigation-map.jpg)

3. Select **Relocalize (重定位)**. Both automatic and manual relocalization are supported. Try automatic relocalization first. If it takes too long to complete, switch to manual relocalization: tap the robot's approximate position on the map, then drag the pose marker in the direction the robot is facing.

   Automatic relocalization demo:

   ![type:video](../../assets/elf3/developer/navigation/auto-relocalize-demo.mp4 "Automatic robot relocalization demo")

   Manual relocalization demo:

   ![type:video](../../assets/elf3/developer/navigation/relocalize-robot-demo.mp4 "Manual robot relocalization demo")

4. Check whether the red point cloud around the robot aligns with the walls on the map. If they align, select **Confirm (确认)**. If the offset is significant, adjust the position and heading again.

   ![Adjust the robot position and heading to complete relocalization](../../assets/elf3/developer/navigation/relocalize-robot.jpg)

5. Select **Navigate (导航)** to start the guided-tour task.

   ![Start the navigation task](../../assets/elf3/developer/navigation/start-navigation.jpg)

6. If a problem occurs during the tour, immediately select **Pause (暂停)** or **Stop (终止)**. You can also use the on-screen joystick to take manual control and prevent the robot from continuing off course.

   ![Pause, stop, or manually control the navigation task](../../assets/elf3/developer/navigation/navigation-controls.jpg)

7. When the tour is complete, stop navigation before leaving the page.

## Troubleshooting

### How to Adjust the Remote-Control Speed

1. Open the robot remote-control page and select the **Settings** icon in the upper-right corner.

   ![Open Settings from the remote-control page](../../assets/elf3/developer/navigation/remote-speed-settings-entry.jpg)

2. Select **Control (控制)** on the Settings page, then adjust the following parameters as needed:

   - **Speed Output Range (速度输出范围)**: limits the forward and reverse linear speed for both the on-screen virtual joystick and an external gamepad.
   - **Rotation Output Range (旋转输出范围)**: limits the left and right turning speed for both the on-screen virtual joystick and an external gamepad.

   ![Adjust the speed and rotation output ranges](../../assets/elf3/developer/navigation/remote-speed-output-range.jpg)

After changing the ranges, test the robot at low speed in a clear, safe area. Increase the limits gradually only after confirming that the robot moves as expected.

### The LiDAR Does Not Start

- Confirm that the computer and LiDAR are connected by Ethernet and are on the same subnet.
- Confirm that **Robot Receive IP (机器人接收 IP)** in the app matches the IP address of the robot's network interface connected to the LiDAR.
- Confirm that **LiDAR IP (雷达 IP)** matches the device address found in the search and is on the same subnet as the receive IP.
- Confirm that the configuration was saved successfully and the robot has been restarted.

### People or Dynamic Obstacles Appear on the Map

- Keep the mapping operator behind the robot.
- Minimize pedestrian movement during mapping.
- If people or moving obstacles have been captured in the map, wait for them to leave, then remotely drive the robot through the affected area again so the new version's dynamic obstacle filtering can remove the remaining traces.
- Add clearing zones in the map editor for obstacles that no longer exist.

### The Point Cloud Does Not Align with the Walls After Relocalization

- Select the robot's position on the map again.
- Adjust the pose marker to match the robot's actual heading.
- Start navigation only after the red point-cloud returns are reasonably aligned with the walls.
