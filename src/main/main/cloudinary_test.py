import os

import rclpy
from rclpy.node import Node
from std_msgs.msg import Bool

from ament_index_python.packages import get_package_share_directory

import cloudinary
import cloudinary.uploader

class CloudinaryUploader(Node):
    def __init__(self):
        super().__init__('cloudinary_uploader')
        
        
        cloudinary.config(
            cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
            api_key=os.getenv("CLOUDINARY_API_KEY"),
            api_secret=os.getenv("CLOUDINARY_API_SECRET")
        )

        
        pkg_path = get_package_share_directory('main')
        self.image_path = os.path.join(pkg_path, 'sample_images', 'test.jpg')

        self.state_pub = self.create_publisher(Bool, 'upload_state', 10)

        self.create_timer(1.0, self.upload_image_once)

    def upload_image_once(self):
        try:
            self.get_logger().info(f'Uploading: {self.image_path}')
            result = cloudinary.uploader.upload(self.image_path)
            self.get_logger().info(f'Upload Successful: {result["secure_url"]}')
            self.state_pub.publish(Bool(data=True))

        except Exception as e:
            self.get_logger().error(f'Upload failed: {e}')
            self.state_pub.publish(Bool(data=False))

        self.destroy_timer(self.timer)

def main():
    rclpy.init()
    uploader = CloudinaryUploader()
    rclpy.spin(uploader)
    uploader.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()