import os
import sys
import argparse
import glob

import cv2
from ultralytics import YOLO

# Define and parse user input arguments
parser = argparse.ArgumentParser()
parser.add_argument('--model', help='Path to YOLO model file (example: "runs/detect/train/weights/best.pt")',
                    required=True)
parser.add_argument('--source', help='Image source, can be image file ("test.jpg"), \
                    image folder ("test_dir"), video file ("testvid.mp4"), index of USB camera ("usb0"), or index of Picamera ("picamera0")', 
                    required=True)
parser.add_argument('--thresh', help='Minimum confidence threshold for displaying detected objects (example: "0.4")',
                    default=0.5)

args = parser.parse_args()

# Parse user inputs
model_path = args.model
img_source = args.source
min_thresh = float(args.thresh)

# Check if model file exists and is valid
if not os.path.exists(model_path):
    print(f"ERROR: Model path invalid or file not found: {model_path}")
    sys.exit(1)

print(f"Loading YOLO model from {model_path}...")
model = YOLO(model_path, task='detect')
print("Model loaded successfully.")

# Parse input to determine if image source is a file, folder, video, or USB camera
img_ext_list = ['.jpg', '.JPG', '.jpeg', '.JPEG', '.png', '.PNG', '.bmp', '.BMP']
vid_ext_list = ['.avi', '.mov', '.mp4', '.mkv', '.wmv']

if os.path.isdir(img_source):
    source_type = 'folder'
elif os.path.isfile(img_source):
    _, ext = os.path.splitext(img_source)
    if ext in img_ext_list:
        source_type = 'image'
    elif ext in vid_ext_list:
        source_type = 'video'
    else:
        print(f"ERROR: Unsupported file extension: {ext}")
        sys.exit(1)
elif 'usb' in img_source:
    source_type = 'usb'
    usb_idx = int(img_source[3:])
elif 'picamera' in img_source:
    source_type = 'picamera'
    picam_idx = int(img_source[8:])
else:
    print(f"ERROR: Invalid image source provided: {img_source}")
    sys.exit(1)

print(f"Detected source type: {source_type}")

# Load or initialize image source
if source_type == 'image':
    imgs_list = [img_source]
elif source_type == 'folder':
    imgs_list = []
    filelist = glob.glob(img_source + '/*')
    for file in filelist:
        _, file_ext = os.path.splitext(file)
        if file_ext in img_ext_list:
            imgs_list.append(file)
    print(f"Found {len(imgs_list)} images in folder.")
elif source_type in ['video', 'usb']:
    cap_arg = img_source if source_type == 'video' else usb_idx
    cap = cv2.VideoCapture(cap_arg)
    if not cap.isOpened():
        print(f"ERROR: Failed to open video capture source: {img_source}")
        sys.exit(1)
elif source_type == 'picamera':
    from picamera2 import Picamera2
    cap = Picamera2()
    cap.configure(cap.create_video_configuration(main={"format": 'RGB888'}))
    cap.start()

img_count = 0
frame_count = 0

print("Starting pipeline loop...")

# Begin inference loop
while True:
    # Load frame from image source
    if source_type in ['image', 'folder']:
        if img_count >= len(imgs_list):
            print("All images have been processed.")
            break
        img_filename = imgs_list[img_count]
        frame = cv2.imread(img_filename)
        img_count += 1
        frame_id = img_filename
    
    elif source_type == 'video':
        ret, frame = cap.read()
        if not ret:
            print("Reached end of the video file.")
            break
        frame_count += 1
        frame_id = f"Frame #{frame_count}"
    
    elif source_type in ['usb', 'picamera']:
        if source_type == 'usb':
            ret, frame = cap.read()
            if (frame is None) or (not ret):
                print("ERROR: Unable to read frames from the USB camera.")
                break
        else:
            frame = cap.capture_array()
            if frame is None:
                print("ERROR: Unable to read frames from the Picamera.")
                break
        frame_count += 1
        frame_id = f"Stream Frame #{frame_count}"

    # Run inference on frame
    results = model(frame, verbose=False)
    detections = results[0].boxes

    any_object_detected = False
    valid_detections_count = 0

    # Evaluate detections against target threshold
    for i in range(len(detections)):
        conf = detections[i].conf.item()
        if conf > min_thresh:
            any_object_detected = True
            valid_detections_count += 1

    # Print the requested status and info to console
    print(f"[{frame_id}] Detected: {any_object_detected} | Target Count: {valid_detections_count}")

# Clean up
print("Shutting down and clearing hardware capture contexts.")
if source_type in ['video', 'usb']:
    cap.release()
elif source_type == 'picamera':
    cap.stop()