import serial
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class SerialTest(Node):
    def __init__(self):
        super().__init__('serial_test_node')
        self.get_logger().info('Serial Test Node has been started.')

        self.declare_parameter("serial_port", "/dev/arduino")
        self.declare_parameter("baud_rate", 115200)
        port = self.get_parameter("serial_port").value
        baud_rate = self.get_parameter("baud_rate").value

        try:
            self.ser = serial.Serial(port, baud_rate, timeout=1)
            time.sleep(2)
            self.get_logger().info(f'Connected to serial port: {port}')
        except serial.SerialException as e:
            self.get_logger().error(f'Failed to connect to {port}: {e}')
            self.ser = None

        self.topic_sub = self.create_subscription(
            String, 
            "serial_test", 
            self.serial_callback, 
            10
        )

    def serial_callback(self, msg: String):
        if self.ser is not None and self.ser.is_open:
            try:
                data_to_send = f'{msg.data}\n'.encode('utf-8')
                self.ser.write(data_to_send)
                self.get_logger().info(f"Sent: {msg.data}")
            except Exception as e:
                self.get_logger().error(f"Error writing to serial: {e}")
        else:
            self.get_logger().warn("Serial port not open, cannot send data.")

    def destroy_node(self):
        if self.ser and self.ser.is_open:
            self.ser.close()
            self.get_logger().info("Serial port closed.")
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SerialTest()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()