import cv2
import os
import pika
import json
import base64
import numpy as np
import pathlib
import redis
import re

from google.cloud import vision
from possible_char import PossibleChar
from plate_character_detector import PlateCharacterDetector

os.chdir(pathlib.Path(__file__).parent.absolute())
os.chdir("..")

with open('config.json') as f:
    config = json.load(f)

redis = redis.Redis(
    host=config['redis']['host'], 
    port=config['redis']['port'], 
    password=config['redis']['password'], 
    db=0
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=config['rabbitmq']['host'], port=config['rabbitmq']['port'])
)

channel = connection.channel()

channel.queue_declare(
    queue=config['plate_number_character_detector_service']['routing_key']['detected_plate_number'], 
    durable=True
)

channel.queue_declare(
    queue=config['plate_detector_service']['queue_key']['detected_plate'], 
    durable=True
)

client = vision.ImageAnnotatorClient()
detected_plate_cache_key = config['plate_number_character_detector_service']['cache_key']['detected_plate_number']

def is_pattern_match_plate_number(text):
    pattern = re.compile("^[A-Z]+[0-9]+[A-Z]+$")
    return pattern.match(text) is not None

def callback(ch, method, properties, body):
    routing_key = config['plate_number_character_detector_service']['routing_key']['detected_plate_number']
    print("detected")
    body = json.loads(body)
    image_buffer = np.frombuffer(redis.get(body["image_key"]), dtype=np.uint8)
    image = cv2.imdecode(image_buffer, cv2.IMREAD_COLOR)

    detected_plate_numbers = []
    for plate_coordinate in body['plate_coordinates']:
        try:
            cropped_plate_image = image[plate_coordinate['min_y']:plate_coordinate['min_y'] + plate_coordinate['max_y'], plate_coordinate['min_x']:plate_coordinate['min_x'] + plate_coordinate['max_x']].copy()
            _, content = cv2.imencode(".jpg", cropped_plate_image)
            image = vision.Image(content=content.tobytes())
            response = client.text_detection(image=image)
            text = response.full_text_annotation.text
            splitted_text = text.split("\n")
            
            for possible_plate_number in splitted_text:
                whitespace_stripped_text = possible_plate_number.replace(" ", "")
                if is_pattern_match_plate_number(whitespace_stripped_text):
                    is_plate_detected_in_previously = redis.get("{}.{}".format(detected_plate_cache_key, whitespace_stripped_text))
                    if (is_plate_detected_in_previously is None):
                        redis.set(
                            "{}.{}".format(detected_plate_cache_key, whitespace_stripped_text),
                            whitespace_stripped_text
                        )
                        detected_plate_numbers.append(whitespace_stripped_text)

        except Exception as e:
            print(str(e))
            continue
        
   
    for detected_plate_number in detected_plate_numbers:
        channel.basic_publish(
            exchange='', 
            routing_key=routing_key, 
            body=json.dumps({
                'detected_plate_number': detected_plate_number
            })
        )

channel.basic_consume(
    queue=config["plate_detector_service"]["queue_key"]["detected_plate"], 
    on_message_callback=callback, 
    auto_ack=True
)

channel.start_consuming()
    
    