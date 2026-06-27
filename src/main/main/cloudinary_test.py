import cloudinary
import cloudinary.uploader
import os

import rclpy
from rclpy.node import Node


CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
CLOUD_API_KEY = os.getenv("CLOUDINARY_API_KEY")
CLOUD_API_SECRET = os.getenv("CLOUDINARY_API_SECRET")


class CloudinaryTest(Node):
    def __init__(self):
        super().__init__('cloudinary_test_node')

        cloudinary.config(
            cloud_name=CLOUD_NAME,
            api_key=CLOUD_API_KEY,
            api_secret=CLOUD_API_SECRET
        )

        self.create_timer(3.0, self.timer_callback)
        self.count = 0
    
    def timer_callback(self):
        if self.count == 0:
            result = cloudinary.uploader.upload("/home/shourya/yolo/src/main/sample_images/test.jpeg")
            self.get_logger().info(f"Uploaded: {result['secure_url']}")
            self.count = 1

        else:
            self.get_logger().info("Image already uploaded, shutting down.")
            raise SystemExit

def main():
    rclpy.init()
    node = CloudinaryTest()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
