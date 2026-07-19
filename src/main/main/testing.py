import os
import sys
import argparse
import time

#Image Processing
import cv2

#Serial
import serial

#YOLO pkgs
from ultralytics import YOLO

#Firebase
import firebase_admin
from firebase_admin import db, credentials

#Cloudinary
import cloudinary
import cloudinary.uploader

#Logging
from datetime import datetime


import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TwistStamped
from sensor_msgs.msg import Imu
from rclpy.qos import QoSProfile, QoSDurabilityPolicy, QoSReliabilityPolicy


# CONSTANTS
OUTPUT_DIR = "/home/shourya/yolo/src/main/clicked_images_inference"
CLICKED_DIR = "/home/shourya/yolo/src/main/clicked_images"
CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")
API_KEY = os.getenv("CLOUDINARY_API_KEY")
API_SECRET = os.getenv("CLOUDINARY_API_SECRET")
PORT = '/dev/arduino'
BAUD_RATE = 115200


def log_to_file(message: str, severity: str = "d"):
    """
    Appends a timestamped message to debug_log.txt.
    Severity 'e': ERROR with dashes.
    Severity 'w': WARN.
    Default 'd': Standard log.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    if severity.lower() == "e":
        log_entry = f"[{timestamp}] ERROR ----------{message}----------\n"
    elif severity.lower() == "w":
        log_entry = f"[{timestamp}] WARN {message}\n"
    else:
        log_entry = f"[{timestamp}] {message}\n"
    
    with open("/home/shourya/yolo/src/main/logs/debug_log.txt", "a") as f:
        f.write(log_entry)

class SerialOperation:
    def __init__(self, port, baudrate):
        #self.arduino = serial.Serial(port, baudrate)
        log_to_file(f"initialised serial at {port} with {baudrate}")

    def send_serial_data(self, direction: str):
        commands = {
            "forward": "rp10.00,lp10.00,\r\n",
            "backward": "rn10.00,ln10.00,\r\n",
            "left": "rp10.00,ln10.00,\r\n",
            "right": "rn10.00,lp10.00\r\n",
            "stop": "rp0.00,lp0.00,\r\n"
        }
        message = commands.get(direction)
        if message:
            self.arduino.write(message.encode('utf-8'))
            log_to_file(f"sent message to arduino with msg: {message}")
        else:
            self.get_logger().info("Direction argument fits no options, please recheck")
            log_to_file("wrong direction passed in send_serial_data(), ignoring command", "w")

class Updatation:
    def __init__(self):
        self.initalise_cloudinary()
        self.initialise_firebase()

    def initalise_cloudinary(self):
        cloudinary.config(cloud_name=CLOUD_NAME, api_key=API_KEY, api_secret=API_SECRET)
        log_to_file("initialised cloudinary")

    def initialise_firebase(self):
        cred = credentials.Certificate("/home/shourya/yolo/src/main/firebase/firebase_new.json")
        firebase_admin.initialize_app(cred, {"databaseURL": "https://testing-65588-default-rtdb.firebaseio.com/"})
        log_to_file("initialised firebase")

    def update_firebase_objects_detect(self, desired_state, desired_number, iteration):
        db.reference(f"/objects/object_detected{iteration}").set(desired_state)
        db.reference(f"/objects/no_objects{iteration}").set(desired_number)
        log_to_file("updated object's number to firebase")

    def update_firebase_url(self, image_raw, infer_image, iteration):
        result1 = cloudinary.uploader.upload(image_raw)
        result2 = cloudinary.uploader.upload(infer_image)
        db.reference(f"/images/input{iteration}").set(result1["secure_url"])
        db.reference(f"/images/inference{iteration}").set(result2["secure_url"])
        log_to_file("uploaded image to cloudinary and stored url in firebase")

class YoloInference():
    def __init__(self):
        log_to_file("initialised YOLO inference class")

    def load_model(self, model_path):
        if not os.path.exists(model_path):
            log_to_file("could not find path to model as specified", "e")
            sys.exit(1)

        log_to_file("model exists in path specified, returning YOLO object")
        return YOLO(model_path, task='detect')

    def determine_source_type(self, img_source):
        # Support both index (e.g., '0') and path (e.g., '/dev/camera')
        if img_source.isdigit() or img_source == '/dev/camera': 
            log_to_file("source is camera")
            return 'camera'
        elif os.path.isdir(img_source): 
            log_to_file("source is folder")
            return 'folder'
        elif os.path.isfile(img_source): 
            log_to_file("source is image")
            return 'image'
        else:
            self.get_logger(f"Error: '{img_source}' is not a valid camera index, folder, or file.")
            log_to_file("source is not valid in determine_source_type()", "e")
            sys.exit(1)

class ImageProcessing:
    def __init__(self, updater):
        self.updater = updater
        log_to_file("initialised image processing class with updater")

    def get_and_increment_counter(self):
        counter_file = os.path.join("/home/shourya/yolo/src/main/setup", "counter_inference.txt")
        os.makedirs("/home/shourya/yolo/src/main/setup", exist_ok=True)
        count = 1
        if os.path.exists(counter_file):
            with open(counter_file, "r") as f:
                try:
                    current_val = int(f.read().strip())
                    count = ((current_val - 1) % 4) + 1
                except ValueError:
                    count = 1
        with open(counter_file, "w") as f:
            f.write(str(count + 1 if count < 4 else 1))
        return count

    def open_camera(self, camera_input):
        cap = cv2.VideoCapture(camera_input)
        if not cap.isOpened(): 
            log_to_file(f"could not open camera, check source specified {camera_input}", "e")
            sys.exit(1)
        
        log_to_file("opened camera successfully")
        return cap

    def take_picture_from_camera(self, cap, model, min_thresh):
        pic_count = self.get_and_increment_counter()
        folder_name = f"pic{pic_count}"
        
        current_raw_dir = os.path.join(CLICKED_DIR, folder_name)
        current_infer_dir = os.path.join(OUTPUT_DIR, folder_name)
        
        os.makedirs(current_raw_dir, exist_ok=True)
        os.makedirs(current_infer_dir, exist_ok=True)
        
        for folder in [current_raw_dir, current_infer_dir]:
            for filename in os.listdir(folder):
                file_path = os.path.join(folder, filename)
                if os.path.isfile(file_path): os.unlink(file_path)
        
        for _ in range(2): cap.read()
        ret, frame = cap.read()
        
        if not ret: 
            log_to_file("raised a IOerror error, failed to capture image", "e")
            raise IOError(f"Failed to capture image from camera at iteration {pic_count}")

        raw_save_path = os.path.join(current_raw_dir, "captured_image_raw.jpg")
        cv2.imwrite(raw_save_path, frame)
        log_to_file(f"wrote image of raw image to path {raw_save_path}")

        results = model(frame, verbose=False)
        detections = results[0].boxes
        
        any_object_detected = False
        valid_detections_count = 0
        for i in range(len(detections)):
            if detections[i].conf.item() > min_thresh:
                any_object_detected = True
                valid_detections_count += 1

        annotated_frame = results[0].plot()
        infer_save_path = os.path.join(current_infer_dir, "captured_image_inferenced.jpg")
        cv2.imwrite(infer_save_path, annotated_frame)
        log_to_file(f"wrote image of inferenced image to {infer_save_path}")

        self.updater.update_firebase_objects_detect(any_object_detected, valid_detections_count, pic_count)
        log_to_file(f"updated firebase object's no in take_picture_from_camera()")

        print(f"objects {valid_detections_count}")
        log_to_file(f"objects detected on iteration {pic_count}: {valid_detections_count}")
        
        if any_object_detected:
            self.updater.update_firebase_url(raw_save_path, infer_save_path, pic_count)
            log_to_file("updated firebase url for images in take_picture_from_camera()")


class MainNode(Node):
    def __init__(self):
        super().__init__('main_node')
        self.declare_parameter('model', '/path/to/default/model.pt')
        self.declare_parameter('source', '0')
        self.declare_parameter('thresh', 0.5)

        self.qos_profile_pub = QoSProfile(depth=5)
        self.qos_profile_pub.reliability = QoSReliabilityPolicy.BEST_EFFORT
        self.qos_profile_pub.durability = QoSDurabilityPolicy.VOLATILE

        self.cmd_vel_pub = self.create_publisher(TwistStamped, "/input_joy/cmd_vel_stamped", 10)
        self.imu_sub = self.create_subscription(Imu, "/imu/out", self.imu_callback, self.qos_profile_pub)

        self.timer_ = self.create_timer(1.0, self.timer_callback)

        log_to_file("ROS2 node initialized with params")
        self.ang_vel = 0.0

    def imu_callback(self, msg):
        self.ang_vel = msg.angular_velocity.z
        self.get_logger().info(f"Received IMU data")

    def send_command_movement(self, direction):
        direction = direction.lower()
        message = TwistStamped()
        message.header.stamp = self.get_clock().now().to_msg()
        message.header.frame_id = "key_teleop"

        if direction == "forward":
            message.twist.linear.x = 0.5
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = 0.0
            self.get_logger().info("in forward")
            
        elif direction == "backward":
            message.twist.linear.x = -0.5
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = 0.0
            self.get_logger().info("in backward")

        elif direction == "right":
            message.twist.linear.x = 0.0
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = -1.0
            self.get_logger().info("in right")

        elif direction == "right_minor":
            message.twist.linear.x = 0.0
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = -0.5
            self.get_logger().info("in right_minor")

        elif direction == "left":
            message.twist.linear.x = 0.0
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = 1.0 
            self.get_logger().info("in left")
        
        elif direction == "left_minor":
            message.twist.linear.x = 0.0
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = 0.4
            self.get_logger().info("in left_minor")

        elif direction == "stop":
            message.twist.linear.x = 0.0
            message.twist.linear.y = 0.0
            message.twist.linear.z = 0.0
            message.twist.angular.x = 0.0
            message.twist.angular.y = 0.0
            message.twist.angular.z = 0.0
            self.get_logger().info("in stop")

        else:
            self.get_logger().info("wrong argument passed to send_command+message()")   

        self.cmd_vel_pub.publish(message)
        self.get_logger().info("publishing message")

    def timer_callback(self):
        log_to_file("----------------------------CODE EXECUTION START----------------------------")
        updater = Updatation()
        serial_op = SerialOperation(PORT, BAUD_RATE)
        yolo_handler = YoloInference()
        img_proc = ImageProcessing(updater)

        # Retrieve parameters
        model_path = self.get_parameter('model').get_parameter_value().string_value
        img_source = self.get_parameter('source').get_parameter_value().string_value
        min_thresh = self.get_parameter('thresh').get_parameter_value().double_value

        model = yolo_handler.load_model(model_path)
        source_type = yolo_handler.determine_source_type(img_source)


        if source_type == 'camera':
            if img_source == '/dev/camera' :
                camera_input = img_source 

            else:
                camera_input = int(img_source)

            cap = img_proc.open_camera(camera_input)

        for n in range(1, 2):
            self.get_logger().info(f"-------------------number for n is : {n}------------------------")
            log_to_file(f"-------------------number for n is : {n}------------------------")

            #----------------------A starts-------------------------
            # start_time = time.time() #0
            # while time.time() - start_time < 3:
            #     self.send_command_movement("forward")
            #     time.sleep(0.1)
            
            time.sleep(2)
            
            while self.ang_vel < 0.167:
                self.send_command_movement("right") 

            # try: 
            #     img_proc.take_picture_from_camera(cap, model, min_thresh)
            # except IOError as e: 
            #     self.get_logger().info(f"error in take_picture_from_camera: {e}")
            #     log_to_file(f"error in take_picture_from_camera: {e}", "e")
            #     sys.exit(1)

            # self.send_command_movement("left")
            # time.sleep(2.0)
            # self.send_command_movement("left_minor")
            # time.sleep(2.0)

            # start_time = time.time() #0
            # while time.time() - start_time < 3:
            #     self.send_command_movement("forward")
            #     time.sleep(0.1)
            
            # time.sleep(2)

            # #----------------------A ends-------------------------
            # #----------------------B starts-------------------------

            # self.send_command_movement("right")
            # time.sleep(2.0)
            # self.send_command_movement("right_minor")
            # time.sleep(2.0)

            # if n == 4:
            #     cap.release()
            #     log_to_file("closed camera connection")

        log_to_file("----------------------------CODE EXECUTION END----------------------------")
        self.timer_.cancel()
        # raise SystemExit


def main():
    rclpy.init()
    main_node = MainNode()
    rclpy.spin(main_node)
    main_node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()