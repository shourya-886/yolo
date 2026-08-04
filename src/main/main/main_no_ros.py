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


# CONSTANTS
OUTPUT_DIR = "clicked_images_inference"
CLICKED_DIR = "clicked_images"
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
        self.arduino = serial.Serial(port, baudrate)
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
            print("Direction argument fits no options, please recheck")
            log_to_file("wrong direction passed in send_serial_data(), ignoring command", "w")

class Updatation:
    def __init__(self):
        self.initalise_cloudinary()
        self.initialise_firebase()

    def initalise_cloudinary(self):
        cloudinary.config(cloud_name=CLOUD_NAME, api_key=API_KEY, api_secret=API_SECRET)
        log_to_file("initialised cloudinary")

    def initialise_firebase(self):
        cred = credentials.Certificate("/home/shourya/yolo/src/main/firebase/firebase_new_new.json")
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

class YoloInference:
    def define_and_parse_args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('--model', required=True)
        parser.add_argument('--source', required=True)
        parser.add_argument('--thresh', default=0.5)
        args = parser.parse_args()
        model = args.model
        source = args.source
        thresh = float(args.thresh)
        log_to_file(f"parsed arguments with {source} and {model} and {thresh}")
        return model, source, thresh

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
            print(f"Error: '{img_source}' is not a valid camera index, folder, or file.")
            log_to_file("source is not valid in determine_source_type()", "e")
            sys.exit(1)

class ImageProcessing:
    def __init__(self, updater, serial_op):
        self.updater = updater
        self.serial_op = serial_op

    def get_and_increment_counter(self):
        counter_file = os.path.join("setup", "counter_inference.txt")
        os.makedirs("setup", exist_ok=True)
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
            log_to_file("could not open camera, check source specified", "e")
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
        
        # Raise an exception if the frame could not be captured
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

def main():
    log_to_file("----------------------------CODE EXECUTION START----------------------------")
    updater = Updatation()
    serial_op = SerialOperation(PORT, BAUD_RATE)
    yolo_handler = YoloInference()
    img_proc = ImageProcessing(updater, serial_op)

    model_path, img_source, min_thresh = yolo_handler.define_and_parse_args()
    model = yolo_handler.load_model(model_path)
    source_type = yolo_handler.determine_source_type(img_source)


    if source_type == 'camera':
        if img_source == '/dev/camera' :
            camera_input = img_source 

        else:
            camera_input = int(img_source)

        cap = img_proc.open_camera(camera_input)

    for n in range(1, 5):
        print(f"-------------------number for n is : {n}------------------------")
        log_to_file(f"-------------------number for n is : {n}------------------------")
        serial_op.send_serial_data("forward")
        time.sleep(3)
        serial_op.send_serial_data("stop")
        
        serial_op.send_serial_data("right")
        time.sleep(0.5) 
        serial_op.send_serial_data("stop")
        try: 
            img_proc.take_picture_from_camera(cap, model, min_thresh)
        except IOError as e: 
            print(f"error in take_picture_from_camera: {e}")
            log_to_file(f"error in take_picture_from_camera: {e}", "e")
            sys.exit(1)

        serial_op.send_serial_data("left")
        time.sleep(0.5)
        serial_op.send_serial_data("stop")
        
        serial_op.send_serial_data("forward")
        time.sleep(1)
        serial_op.send_serial_data("stop")

        if n == 4:
            cap.release()
            log_to_file("closed camera connection")

    log_to_file("----------------------------CODE EXECUTION END----------------------------")

if __name__ == '__main__':
    main()