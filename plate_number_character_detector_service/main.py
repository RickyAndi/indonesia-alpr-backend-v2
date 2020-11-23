import cv2
import os
import pika
import json
import base64
import numpy as np

import possible_chars

from rejson import Client, Path
from plate_character_detector import PlateCharacterDetector

os.chdir(pathlib.Path(__file__).parent.absolute())
os.chdir("..")

with open('config.json') as f:
    config = json.load(f)

rj = Client(
    host=config['redis']['host'], 
    port=config['redis']['port'], 
    decode_responses=True
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=config['rabbitmq']['host'], port=config['rabbitmq']['port'])
)

channel = connection.channel()
channel.exchange_declare(
    exchange=config['rabbitmq']['exchange'], 
    exchange_type=config['rabbitmq']['exchange_type']
)

result = channel.queue_declare(queue='', exclusive=True)
channel.queue_bind(
    exchange=config['rabbitmq']['exchange'],
    queue=result.method.queue,
    routing_key=config['plate_detector_service']['routing_key']['detected_plate']
)

train_data = np.loadtxt(config['plate_number_character_detector_service']['knn']['train']['data'], np.float32)
labels = np.loadtxt(config['plate_number_character_detector_service']['knn']['train']['labels'], np.float32)
train_data = train_data.reshape((train_data.size, 1))

plate_character_detector = PlateCharacterDetector(knn_k = 1)
plate_character_detector.trainKnn(train_data=train_data, labels=labels)

def callback(ch, method, properties, body):

    body = json.loads(body)
    image = base64.b64decode(body['image'])
    image = np.fromstring(image, np.uint8)
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)

    detected_plate_numbers = []
    for plate_coordinate in body['plate_coordinates']:
        image = image[plate_coordinate['min_x']:plate_coordinate['min_x'] + plate_coordinate['min_x'] + plate_coordinate['max_x'], plate_coordinate['min_y']:plate_coordinate['min_y'] + plate_coordinate['max_y']]
        plate_number = plate_character_detector.detectCharacterInPlate(image)
        detected_plate_numbers.append(plate_number)
    
    cache_key = config['plate_number_character_detector_service']['cache_key']['detected_plate_number']   
    routing_key = config['plate_number_character_detector_service']['routing_key']['detected_plate_number']
            
    for plate_number in detected_plate_numbers:

        cached_plate_number = rj.jsonmget(cache_key, Path("{}".format(plate_number)))
        
        if cached_plate_number is None:
            
            plate_number_cache = {}
            plate_number_cache[plate_number] = plate_number
            
            rj.jsonset(cache_key, Path.rootPath(), plate_number_cache)

            channel.basic_publish(
                exchange=config['rabbitmq']['exchange'], 
                routing_key=routing_key, 
                body=json.dumps({
                    'plate_number': plate_number
                })
            )

channel.basic_consume(
    queue=result.method.queue, on_message_callback=callback, auto_ack=True)

channel.start_consuming()
    
    