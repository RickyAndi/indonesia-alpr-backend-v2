import os
import pika
import cv2
import json
import base64
import pathlib
import numpy as np
import asyncio
import redis
import time
import random
import string

from threading import Thread
from cnn_model import CNNModel
from image import Image
from image_streamer import ImageStreamer
from multiprocessing import Process
from threading import Thread

os.chdir(pathlib.Path(__file__).parent.absolute())
os.chdir("..")

with open('config.json') as f:
    config = json.load(f)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=config['rabbitmq']['host'])
)
channel = connection.channel()
channel.queue_declare(
    queue=config["plate_detector_service"]["queue_key"]["detected_plate"], 
    durable=True
)

redis = redis.Redis(
    host=config['redis']['host'], 
    port=config['redis']['port'], 
    password="password", 
    db=0
)

def publish_image_with_detected_plates(image_original, plate_coordinates):
    
    letters = string.ascii_lowercase
    random_key = ''.join(random.choice(letters) for i in range(10))

    _, buffer = cv2.imencode(".jpg", image_original)
    redis.set(random_key, buffer.tobytes())
    
    channel.basic_publish(
        exchange='', 
        routing_key=config['plate_detector_service']['routing_key']['detected_plate'],
        body=json.dumps({
            "image_key": random_key,
            'plate_coordinates': plate_coordinates
        })
    )

def main():
    
    cnn_model = CNNModel(
        config['plate_detector_service']['yolo']['model_path'], 
        config['plate_detector_service']['yolo']['weight_path']
    )

    if config['plate_detector_service']['source_type'] == "rtsp":
        capture = cv2.VideoCapture(config['plate_detector_service']['rtsp']['source'], cv2.CAP_FFMPEG)

    if config['plate_detector_service']['source_type'] == "video":
        capture = cv2.VideoCapture(config['plate_detector_service']['video_path'])

    if config['plate_detector_service']['source_type'] == "webcam":
        capture = cv2.VideoCapture(0)
    
    count = 0
    while capture.isOpened():
        
        _, frame = capture.read()

        if count > 20:
            count = 0
            image = Image(frame)
            image_with_predicted_plate = cnn_model.predict_plate_number(image)
            
            if len(image_with_predicted_plate.getPlateCoordinates()) != 0:
                image_original = image_with_predicted_plate.getImage()
                plate_coordinates = map(lambda plate_coordinate: {'min_x': plate_coordinate.getMinX(), 'max_x': plate_coordinate.getWidth(), 'min_y': plate_coordinate.getMinY(), 'max_y': plate_coordinate.getHeight()}, image_with_predicted_plate.getPlateCoordinates())
                publish_image_with_detected_plates(image_original, list(plate_coordinates))
        
        count = count + 1

main()