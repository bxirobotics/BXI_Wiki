# 运动控制开发指南

本文档包含 精灵3 机器人运动控制开发说明。

---

## 机器人的使用
```
#机器人主控的根目录下有bxi_ws文件夹，里面带有机器人的运动控制程序

#附项目的原地址,请仔细阅读readme.md
https://github.com/bxirobotics/bxi_rl_controller_ros2_example
```
## 启动机器人程序
- 启动仿真程序
```
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch bxi_example_py_elf3 example_launch_demo.py
```
- 启动真机程序（**注意安全**）
```
# 需要和机器人电机交互的程序因为权限问题都需要进入root

# 进入root
sudo su 

source /opt/bxi/bxi_ros2_pkg/setup.bash
cd /home/bxi/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch bxi_example_py_elf3 example_launch_demo_hw.py
```
![alt text](../../assets/elf3/motion1.png)<br>
启动后电机会上电,观察全身电机会有绿灯,机器人会进入自检，如果6s左右后绿灯没有熄灭说明自检通过<br>
- 启动遥控器程序
```
#真机
sudo su 
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd /home/bxi/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch remote_controller remote_conroller_launch.py 

#仿真
source /opt/bxi/bxi_ros2_pkg/setup.bash
cd ~/bxi_ws/bxi_rl_controller_ros2_example
source install/setup.bash
ros2 launch remote_controller remote_conroller_launch.py 

```
## 二次开发指南
### 如何引入自定义控制器
-  **重要**：关闭机器人自启动服务
```
    systemctl stop ros_elf_launch.service
```
发布的消息类型<br>
机器启动的时候会订阅 /motion_commands 话题
该消息类型为自定义消息在bxi_ros2_pkg里面：**communication/msg/MotionCommands**
```
#communication/msg/MotionCommands 内容
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
#### C++ 示例
**1.创建工作环境**
```
# my_cpp_pkg 自行修改名字
ros2 pkg create my_cpp_pkg --build-type ament_cmake --dependencies rclcpp std_msgs
```
**2. 示例代码**<br>
进入到src里面创建 main.cpp,同时记得修改CmakeList.txt<br>
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
        message.vel_des.x =  0.5; // 前后
        message.yawdot_des =  0.5;// 旋转

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
**3.使用方法**
```
# 需要在先colcon build 编译后再进行一下操作
source install/setup.bash
ros2 run my_cpp_pkg cpp_node
```
即可正常发布
#### Python 示例
**1.创建工作环境**
```
# my_cpp_pkg 自行修改名字
ros2 pkg create my_py_pkg --build-type ament_python --dependencies rclpy std_msgs
```
**2.示例代码**<br>
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
#添加这个
 <depend>communication</depend>
```
**setup.py**
```
# 修改入口
entry_points={
    'console_scripts': [
        'motion_ctrl = my_py_pkg.motion_ctrl:main',
    ],
},
```
**3.使用方法**

```
#需要在先colcon build 编译后再进行一下操作
source install/setup.bash
ros2 run my_py_pkg motion_ctrl
```

# 常见问题
### 1.如何关闭后台遥控器服务
机器人上电的时候会自动启动遥控器服务方便平常调试与演示<br>
- 查询服务状态
```
systemctl status ros_elf_launch.service
```
![alt text](../../assets/elf3/motionservice.png)<br>
关掉它有以下办法<br>
- 暂时关闭
```
systemctl stop ros_elf_launch.service
```
- 再启动
```
systemctl start ros_elf_launch.service
```
- 永久关闭
```
systemctl stop ros_elf_launch.service
sudo systemctl disable ros_elf_launch.service
#这个会禁用开机自启
```
### 2.真机程序启动失败后日志查看

- 官方程序会把日志放在 /var/log/bxi_log路径内，按照时间排序
