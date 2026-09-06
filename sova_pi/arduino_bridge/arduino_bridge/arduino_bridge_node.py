import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial

class ArduinoBridgeNode(Node):
    def __init__(self):
        super().__init__('arduino_bridge_node')

        self.arduino = serial.Serial('/dev/ttyACM0', 1000000, timeout=1)
        self.has_announced_found = False

        self.search_sub_ = self.create_subscription(
            String, 'search_targets', self.search_callback, 10)

        self.coord_sub_ = self.create_subscription(
            String, 'target_coordinates', self.coord_callback, 10)

        self.get_logger().info("arduino bridge node ready")

    def search_callback(self, msg):
        self.has_announced_found = False
        self.arduino.write(b"SEARCH\n")
        self.get_logger().info("sent SEARCH command to arduino")

    def coord_callback(self, msg):
        x, y, z = msg.data.split(',')
        distance_m = int(z) / 1000.0

        if not self.has_announced_found:
            self.arduino.write(b"FOUND\n")
            self.has_announced_found = True
            self.get_logger().info("sent FOUND to arduino")

        command = f"DIST,{distance_m:.2f}\n"
        self.arduino.write(command.encode())
        self.get_logger().info(f"sent {command.strip()} to arduino")


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()