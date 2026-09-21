import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial

SWEEP_LOW = 400
SWEEP_HIGH = 1000
CENTER_ANGLE = 600
DEAD_ZONE = 5
NUDGE_STEP = 25
MIN_ANGLE = 0
MAX_ANGLE = 1200
DIRECTION = 1 

class ArduinoBridgeNode(Node):
    def __init__(self):
        super().__init__('arduino_bridge_node')

        self.arduino = serial.Serial('/dev/ttyACM0', 1000000, timeout=1)
        self.has_announced_found = False
        self.is_searching = False
        self.sweep_target = SWEEP_HIGH
        self.current_angle = CENTER_ANGLE

        self.search_sub_ = self.create_subscription(
            String, 'search_targets', self.search_callback, 10)
        self.coord_sub_ = self.create_subscription(
            String, 'target_coordinates', self.coord_callback, 10)
        self.offset_sub_ = self.create_subscription(
            String, 'target_offset', self.offset_callback, 10)

        self.sweep_timer_ = self.create_timer(2.0, self.sweep_step)

        self.get_logger().info("arduino bridge node ready")

    def send_angle(self, angle):
        angle = max(MIN_ANGLE, min(MAX_ANGLE, angle))
        self.arduino.write(f"ANGLE,{angle}\n".encode())
        self.current_angle = angle

    def search_callback(self, msg):
        self.has_announced_found = False
        self.is_searching = True
        self.arduino.write(b"SEARCH\n")
        self.get_logger().info("sent SEARCH command to arduino")

    def sweep_step(self):
        if not self.is_searching:
            return
        self.send_angle(self.sweep_target)
        self.sweep_target = SWEEP_LOW if self.sweep_target == SWEEP_HIGH else SWEEP_HIGH

    def coord_callback(self, msg):
        x, y, z = msg.data.split(',')
        distance_m = int(z) / 1000.0

        if not self.has_announced_found:
            self.is_searching = False
            self.arduino.write(b"FOUND\n")
            self.has_announced_found = True
            self.get_logger().info("sent FOUND to arduino")

        command = f"DIST,{distance_m:.2f}\n"
        self.arduino.write(command.encode())
        self.get_logger().info(f"sent {command.strip()} to arduino")

    def offset_callback(self, msg):
        if self.is_searching or not self.has_announced_found:
            return

        offset = float(msg.data)
        if abs(offset) <= DEAD_ZONE:
            return

        step = NUDGE_STEP if offset > 0 else -NUDGE_STEP
        step *= DIRECTION
        new_angle = self.current_angle + step

        self.send_angle(new_angle)
        self.get_logger().info(f"nudged servo to {new_angle} based on offset {offset:.1f}")


def main(args=None):
    rclpy.init(args=args)
    node = ArduinoBridgeNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()