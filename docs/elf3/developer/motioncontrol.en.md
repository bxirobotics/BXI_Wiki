# Motion Control Development Guide

This document provides development instructions for motion control of the Elf3 robot.

---

## Using the Robot
```
#There is a bxi_ws folder in the root directory of the robot controller,which contains the robot motion control program.

#Original project repository. Please read the README.md carefully:
https://github.com/bxirobotics/bxi_rl_controller_ros2_example
```
## Launching the Robot Program
- Start Simulation Program
```
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch bxi_example_py_elf3 example_launch_demo.py
```
- Start Real Robot Program (⚠️ Pay Attention to Safety)
```
# Programs interacting with robot motors require root privileges

# Switch to root
sudo su 

source /opt/bxi/bxi_ros2_pkg/setup.bash
cd /home/bxi/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch bxi_example_py_elf3 example_launch_demo_hw.py
```
![alt text](../../assets/elf3/motion1.png)<br>
After startup, the motors will be powered on. You will observe green lights on all motors.
The robot will enter a self-check process.
If the green lights turn off after about 6 seconds, it indicates that the self-check has passed.<br>
- Start Remote Controller Program
```
#Real Robot
sudo su 
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd /home/bxi/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch remote_controller remote_conroller_launch.py 

#Simulation
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd ~/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch remote_controller remote_conroller_launch.py 

```
## Secondary Development Guide
### How to Integrate Your Own Controller
-  **Important**：Disable the robot auto-start service
```
    systemctl stop ros_elf_launch.service
```
**Message Type to Publish**
When the robot starts, it subscribes to the **/motion_commands** topic.
The message type is a custom message defined in **/bxi_ros2_pkg**：**communication/msg/MotionCommands**
```
#communication/msg/MotionCommands content
std_msgs/Header header
	builtin_interfaces/Time stamp
		int32 sec
		uint32 nanosec
	string frame_id
geometry_msgs/Vector3 vel_des
	float64 x
	float64 y
	float64 z
float32 height_des
float32 yawdot_des
int32 mode
int32 btn_1
int32 btn_2
int32 btn_3
int32 btn_4
int32 btn_5
int32 btn_6
int32 btn_7
int32 btn_8
int32 btn_9
int32 btn_10
int32 axis_1
int32 axis_2
int32 axis_3
int32 axis_4
int32 axis_5
int32 axis_6
int32 axis_7
int32 axis_8
int32 axis_9
int32 axis_10
```
#### C++ Example
**1.Create Workspace**
```
# You can change the package name (my_cpp_pkg)
ros2 pkg create my_cpp_pkg --build-type ament_cmake --dependencies rclcpp std_msgs
```
**2. Example Code**<br>
Create main.cpp under src/ and modify CMakeLists.txt.<br>
**main.cpp**
```
# include "rclcpp/rclcpp.hpp"
# include "std_msgs/msg/string.hpp"
# include <communication/msg/motion_commands.hpp>
using namespace std::chrono_literals;
class MotionCtrl : public rclcpp::Node
{
public:
    MotionCtrl() : Node("motion_ctrl")
    {
        publisher_  = this->create_publisher<communication::msg::MotionCommands>("/motion_commands", 20);
        timer_ = this->create_wall_timer(500ms, std::bind(&MotionCtrl::timer_callback, this));
    }
private:
    void timer_callback()
    {       
        auto message = communication::msg::MotionCommands();
        message.header.stamp = this->get_clock()->now();
        message.header.frame_id = "";
        message.vel_des.x =  0.5; // forward/backward
        message.yawdot_des =  0.5;// rotation

        publisher_->publish(message);
    }
    rclcpp::Publisher<communication::msg::MotionCommands>::SharedPtr publisher_;
    rclcpp::TimerBase::SharedPtr timer_;
};
int main(int argc, char **argv)
{
    rclcpp::init(argc, argv);
    rclcpp::spin(std::make_shared<MotionCtrl>());
    rclcpp::shutdown();
    return 0;
}
```
**CMakeLists.txt**
```
# 添加以下内容
find_package(communication REQUIRED)
add_executable(cpp_node src/main.cpp)
ament_target_dependencies(cpp_node rclcpp std_msgs communication)

install(TARGETS
  cpp_node
  DESTINATION lib/${PROJECT_NAME}
)

```
**3.Usage**
```
# Build first 
# Then run
source install/setup.bash
ros2 run my_cpp_pkg cpp_node
```
#### Python Example
**1.Create Workspace**
```
# You can change the package name (my_py_pkg)
ros2 pkg create my_py_pkg --build-type ament_python --dependencies rclpy std_msgs
```
**2.Example Code**<br>
**main.py**
```
import rclpy
from rclpy.node import Node
from communication.msg import MotionCommands


class MotionCtrl(Node):
    def __init__(self):
        super().__init__('motion_ctrl')

        self.publisher_ = self.create_publisher(
            MotionCommands,
            '/motion_commands',
            20,
        )
        self.timer = self.create_timer(0.5, self.timer_callback)

    def timer_callback(self):
        message = MotionCommands()

        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = ''

        message.vel_des.x = 0.5
        message.yawdot_des = 0.5

        self.publisher_.publish(message)

def main(args=None):
    rclpy.init(args=args)
    node = MotionCtrl()

    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()

```
**package.xml**
```
<!-- Add this -->
 <depend>communication</depend>
```
**setup.py**
```
# Modify entry point
entry_points={
    'console_scripts': [
        'motion_ctrl = my_py_pkg.motion_ctrl:main',
    ],
},
```
**3.Usage**

```
#first build
source install/setup.bash
ros2 run my_py_pkg motion_ctrl
```
# Common Issues
### 1.How to Stop the Background Remote Controller Service
If the green lights remain on after about 6 seconds, it means the self-check has passed.<br>
- Check Service Status
```
systemctl status ros_elf_launch.service
```
![alt text](../../assets/elf3/motionservice.png)<br>
You can stop it using the following methods:<br>
- Stop the Service Temporarily
```
systemctl stop ros_elf_launch.service
```
- Restart the Service
```
systemctl start ros_elf_launch.service
```
- Disable Permanently
```
systemctl stop ros_elf_launch.service
sudo systemctl disable ros_elf_launch.service
#This disables auto-start on boot
```
### 2.Viewing Logs When Real Robot Program Fails to Start

- The official program stores logs in the following directory:
```
/var/log/bxi_log
```
Logs are sorted by time.

