from mysql import connector
import pika
import json
import datetime
import os
import pathlib

os.chdir(pathlib.Path(__file__).parent.absolute())
os.chdir("../..")

with open('config.json') as f:
    config = json.load(f)

connection = connector.connect(
    host=config["mysql"]["host"],
    user=config["mysql"]["username"],
    password=config["mysql"]["password"],
    database=config["mysql"]["database"],
    autocommit=True
)
cursor = connection.cursor(dictionary=True)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=config['rabbitmq']['host'])
)

channel = connection.channel()
channel.exchange_declare(
    exchange=config['rabbitmq']['exchange'], 
    exchange_type=config['rabbitmq']['exchange_type']
)

routing_key = config['plate_number_character_detector_service']['routing_key']['detected_plate_number']
result = channel.queue_declare(queue='', exclusive=True)
channel.queue_bind(
    exchange=config['rabbitmq']['exchange'],
    queue=result.method.queue,
    routing_key=routing_key
)

def callback(ch, method, properties, body):
    body = json.loads(body)
    cursor.execute("SELECT id FROM stolen_plates WHERE plate_number = %s", (body['plate_number'],))
    stolen_plate_numbers = cursor.fetchall()

    if len(stolen_plate_numbers) != 0:

        cursor.execute("SELECT id FROM cameras WHERE name = %s", (body['camera_name'],))
        camera = cursor.fetchone()

        if camera is not None:
            sql = "INSERT INTO detected_stolen_plates (stolen_plate_id, detected_time) VALUES (%s, %s)"
            values = (stolen_plate_numbers[0]['id'], camera['id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            cursor.execute("INSERT INTO detected_stolen_plates (stolen_plate_id, camera_id, detected_time) VALUES (%s, %s, %s)", values)
            
            routing_key = "{}".format(config['plate_number_service']['routing_key']['detected_stolen_plate'])
            channel.basic_publish(
                exchange=config['rabbitmq']['exchange'], 
                routing_key=routing_key, 
                body=json.dumps({
                    'camera_name': body['camera_name'],
                    'plate_number': plate_number
                })
            )


channel.basic_consume(
    queue=result.method.queue, on_message_callback=callback, auto_ack=True)

channel.start_consuming()