import os
import sys

import cv2
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import Image
from cv_bridge import CvBridge


class ImagePublisherNode(Node):

    def __init__(self):
        super().__init__('image_publisher_node')


        self.declare_parameter('path',      '')     
        self.declare_parameter('frequency', 1.0)    
        self.declare_parameter('topic',     '/image')

        path      = self.get_parameter('path').get_parameter_value().string_value
        frequency = self.get_parameter('frequency').get_parameter_value().double_value
        topic     = self.get_parameter('topic').get_parameter_value().string_value


        if not path:
            self.get_logger().fatal("Parameter 'path' is required.")
            sys.exit(1)

        if not os.path.isfile(path):
            self.get_logger().fatal(f"Image file not found: '{path}'")
            sys.exit(1)

        if frequency <= 0.0:
            self.get_logger().fatal("Parameter 'frequency' must be > 0.")
            sys.exit(1)


        self.cv_image = cv2.imread(path)
        if self.cv_image is None:
            self.get_logger().fatal(
                f"cv2.imread failed for '{path}'. "
                "Check the file is a valid image (jpg, png, bmp ...).")
            sys.exit(1)

        self.bridge = CvBridge()


        self.publisher = self.create_publisher(Image, topic, 10)


        period = 1.0 / frequency
        self.timer = self.create_timer(period, self.timer_callback)

        self.get_logger().info(
            f"ImagePublisherNode started | path='{path}' | "
            f"topic='{topic}' | frequency={frequency} Hz")

    def timer_callback(self):
        msg = self.bridge.cv2_to_imgmsg(self.cv_image, encoding='bgr8')
        msg.header.stamp = self.get_clock().now().to_msg()
        self.publisher.publish(msg)


def main(args=None):
    rclpy.init(args=args)
    node = ImagePublisherNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()