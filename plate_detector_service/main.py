import os
import pika
import cv2
import json
import base64

from cnn_model import CNNModel
from image import Image
from image_streamer import ImageStreamer

def main():
    os.chdir(pathlib.Path(__file__).parent.absolute())
    os.chdir("..")

    with open('config.json') as f:
        config = json.load(f)

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=config['rabbitmq']['host'])
    )

    channel = connection.channel()
    channel.exchange_declare(
        exchange=config['rabbitmq']['exchange'], 
        exchange_type=config['rabbitmq']['exchange_type']
    )

    cnn_model = CNNModel(
        config['plate_recognition_service']['yolo']['model_path'], 
        config['plate_recognition_service']['yolo']['weights_path']
    )

    capture = cv2.VideoCapture(config['plate_detector_service']['rtsp']['source'], cv2.CAP_FFMPEG)
    sizeStr = str(int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))) + \
            'x' + str(int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    fps = int(capture.get(cv2.CAP_PROP_FPS))
    image_streamer = ImageStreamer(config['plate_detector_service']['rtsp']['destination'], fps)

    routing_key = config['plate_detector_service']['routing_key']['detected_plate']

    while capture.isOpened():

        _, frame = capture.read()
        image = Image(frame)

        image_with_predicted_plate = cnn_model.predict_plate_number(image)

        image_with_bounding_boxes = image_with_predicted_plate.getImageWithBoundingBoxes()
        _, image_jpg_with_predicted_boxes = cv2.imencode('.jpg', image_with_bounding_boxes)
        image_streamer.send_to_stream(image_jpg_with_predicted_boxes)
        
        image_original = image_with_predicted_plate.getImage()
        image_original_jpg = cv2.imdecode('.jpg', image_original)
        jpg_original_as_text = base64.b64encode(image_original_jpg).decode('ascii')

        plate_coordinates = map(lambda plate_coordinate: {'min_x': plate_coordinate.getX(), 'max_x': plate_coordinate.getMaxX(), 'min_y': plate_coordinate.getY(), 'max_y': plate_coordinate.getMaxY()}, image_with_predicted_plate.getPlateCoordinates())
        
        channel.basic_publish(
            exchange=config['rabbitmq']['exchange'], 
            routing_key=routing_key,
            body=json.dumps({
                'image': jpg_original_as_text,
                'plate_coordinates': plate_coordinates
            })
        )

main()