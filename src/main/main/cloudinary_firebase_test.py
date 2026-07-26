import cloudinary
import cloudinary.uploader

import firebase_admin
from firebase_admin import db, credentials

import rclpy
from rclpy.node import Node


class CloudinaryFirebaseTest(Node):
    def __init__(self):
        super().__init__('cloudinary_firebase_test_node')
        cred = credentials.Certificate("/home/shourya/yolo/src/main/firebase/firebase_new_new.json")
        firebase_admin.initialize_app(cred, {"databaseURL":"https://testing-65588-default-rtdb.firebaseio.com/"}) #this link is for firebase project called wro_2026

        self.timer = self.create_timer(5.0, self.timer_callback)

    def timer_callback(self):
        #creating ref for root
        root_ref = db.reference("/")
        images_ref = db.reference("/images")
        db.reference("/objects/object_detected1").set(True)

def main():
    rclpy.init()
    node = CloudinaryFirebaseTest()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
    