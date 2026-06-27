from datetime import datetime

import rclpy
from rclpy.node import Node

from diagnostic_msgs.msg import KeyValue

class LoggingTestNode(Node):
    def __init__(self):
        super().__init__("logging_test_node")

        self.get_logger().info("Logging Test Node has been started.")

        self.topic_sub = self.create_subscription(
            KeyValue, 
            "logging_test_topic", 
            self.log_callback, 
            10
        )

    def log_callback(self, msg: KeyValue):
        if msg.value.lower() == "error":
            log_level = "e"
        elif msg.value.lower() == "warn":
            log_level = "w"
        else:
            log_level = "d"

        self.log_to_file(f"Received message: {msg.key}", log_level)
        self.get_logger().info(f"Logged message: {msg.key} with severity: {log_level}")

    def log_to_file(self, message: str, severity: str = "d"):

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        if severity.lower() == "e":
            log_entry = f"[{timestamp}] ERROR ----------{message}----------\n"
        elif severity.lower() == "w":
            log_entry = f"[{timestamp}] WARN {message}\n"
        else:
            log_entry = f"[{timestamp}] {message}\n"
        
        
        with open("/home/shourya/yolo/src/main/logs/debug_log.txt", "a") as f:
            f.write(log_entry)

def main(args=None):
    rclpy.init(args=args)
    node = LoggingTestNode()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == "__main__":
    main()