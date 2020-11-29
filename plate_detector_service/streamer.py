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

def main():
    
    if config['plate_detector_service']['source_type'] == "rtsp":
        capture = cv2.VideoCapture(config['plate_detector_service']['rtsp']['source'], cv2.CAP_FFMPEG)

    if config['plate_detector_service']['source_type'] == "video":
        capture = cv2.VideoCapture(config['plate_detector_service']['video_path'])

    if config['plate_detector_service']['source_type'] == "webcam":
        capture = cv2.VideoCapture(0)
        
    sizeStr = str(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))) + \
            'x' + str(int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    image_streamer = ImageStreamer(rtsp_server_url=config['plate_detector_service']['rtsp']['destination'], fps=fps, sizeStr=sizeStr)
    

    while capture.isOpened():
       
        _, frame = capture.read()
        
        _, image_jpg_with_predicted_boxes = cv2.imencode('.png', frame)
        image_streamer.send_to_stream(image_jpg_with_predicted_boxes)

main()