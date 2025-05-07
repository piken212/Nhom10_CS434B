import cv2
import requests
import torch
from ultralytics import YOLO
import numpy as np

# Load the YOLOv8 model
model = YOLO('last_v9.pt')  # Thay bằng đường dẫn tới file last.pt của bạn

# Function to process each frame
def process_frame(frame):
    results = model(frame)  # Dự đoán các đối tượng trong frame
    return results

# Function to calculate intersection-over-union (IoU) of two boxes
def iou(box1, box2):
    x1, y1, x2, y2 = box1
    x1_, y1_, x2_, y2_ = box2

    xi1, yi1 = max(x1, x1_), max(y1, y1_)
    xi2, yi2 = min(x2, x2_), min(y2, y2_)
    inter_area = max(xi2 - xi1 + 1, 0) * max(yi2 - yi1 + 1, 0)

    box1_area = (x2 - x1 + 1) * (y2 - y1 + 1)
    box2_area = (x2_ - x1_ + 1) * (y2_ - y1_ + 1)
    
    union_area = box1_area + box2_area - inter_area

    iou = inter_area / union_area
    return iou

# Function to draw bounding boxes on the frame
def draw_boxes(frame, results):
    boxes = []
    pre = []
    # Collect all boxes
    for result in results[0].boxes:
        x1, y1, x2, y2 = map(int, result.xyxy[0])
        conf = result.conf[0]
        cls = result.cls[0]
        boxes.append((x1, y1, x2, y2, conf, cls))
        pre.append((cls,conf))
    send_predictions(pre)
    # Filter boxes by IoU and confidence
    filtered_boxes = []
    while boxes:
        best_box = max(boxes, key=lambda x: x[4])
        boxes = [box for box in boxes if iou(best_box[:4], box[:4]) < 0.5]
        filtered_boxes.append(best_box)

    # Draw bounding boxes
    for (x1, y1, x2, y2, conf, cls) in filtered_boxes:
        label = f'{model.names[int(cls)]} {conf:.2f}'
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    return frame
def send_predictions(predictions):
    esp32_prediction_url = 'http://192.168.75.196/predict'
    data = "\n".join([f"{pred[0]}: {pred[1]:.2f}" for pred in predictions])
    headers = {'Content-Type': 'text/plain'}
    response = requests.post(esp32_prediction_url, data=data, headers=headers)
    print("Sent predictions:", response.status_code, response.text)