from mysql import connector
import pika
import json
import datetime
import os
import pathlib
import redis

os.chdir(pathlib.Path(__file__).parent.absolute())
os.chdir("../..")

with open('config.json') as f:
    config = json.load(f)

redis = redis.Redis(
    host=config['redis']['host'], 
    port=config['redis']['port'], 
    password=config['redis']['password'], 
    db=0
)

connection = pika.BlockingConnection(
    pika.ConnectionParameters(host=config['rabbitmq']['host'])
)

channel = connection.channel()

channel.queue_declare(
    queue=config['plate_number_character_detector_service']['routing_key']['detected_plate_number'],
    durable=True
)

channel.exchange_declare(
    exchange=config['rabbitmq']['exchange'],
    exchange_type=config['rabbitmq']['exchange_type']
)

def callback(ch, method, properties, body):
    
    connection = connector.connect(
        host=config["mysql"]["host"],
        user=config["mysql"]["username"],
        password=config["mysql"]["password"],
        database=config["mysql"]["database"],
        autocommit=True
    )
    
    cursor = connection.cursor(dictionary=True)

    routing_key = "{}".format(config['plate_number_service']['routing_key']['checked_plate'])
            
    body = json.loads(body)
    detected_plate_number = body['detected_plate_number']
    print(detected_plate_number)
    has_checked_plate_cache_key = config["plate_number_service"]["cache_key"]["has_checked_plate"]
    detected_plate_number_cached_data = redis.get("{}.{}".format(has_checked_plate_cache_key, detected_plate_number))

    if detected_plate_number_cached_data is not None:
        cached_data = json.loads(detected_plate_number_cached_data)
        if cached_data['is_stolen']:

            sql = "INSERT INTO detected_stolen_plates (stolen_plate_id, detected_time) VALUES (%s, %s)"
            values = (detected_plate_number_cached_data['plate_id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            cursor.execute(sql, values)
            

            channel.basic_publish(
                exchange=config['rabbitmq']['exchange'], 
                routing_key=routing_key, 
                body=json.dumps({
                    'is_stolen': True,
                    'plate_number': detected_plate_number
                })
            )
        else:
            channel.basic_publish(
                exchange=config['rabbitmq']['exchange'], 
                routing_key=routing_key, 
                body=json.dumps({
                    'is_stolen': False,
                    'plate_number': detected_plate_number
                })
            )
    else:
        cursor.execute("SELECT id FROM stolen_plates WHERE plate_number = %s", (detected_plate_number,))
        stolen_plate_numbers = cursor.fetchall()

        if len(stolen_plate_numbers) != 0:
            
            sql = "INSERT INTO detected_stolen_plates (stolen_plate_id, detected_time) VALUES (%s, %s)"
            values = (stolen_plate_numbers[0]['id'], datetime.datetime.now().strftime("%Y-%m-%d %H:%M"))
            cursor.execute("INSERT INTO detected_stolen_plates (stolen_plate_id, detected_time) VALUES (%s, %s)", values)
            
            redis.set(
                "{}.{}".format(has_checked_plate_cache_key, detected_plate_number), 
                json.dumps({
                    'plate_id': stolen_plate_numbers[0]['id'],
                    'is_stolen': True
                })
            )
            channel.basic_publish(
                exchange=config['rabbitmq']['exchange'], 
                routing_key=routing_key, 
                body=json.dumps({
                    'plate_number': detected_plate_number,
                    'is_stolen': True
                })
            )

        else:
            redis.set(
                "{}.{}".format(has_checked_plate_cache_key, detected_plate_number), 
                json.dumps({
                    'plate_id': "",
                    'is_stolen': False
                })
            )

            channel.basic_publish(
                exchange=config['rabbitmq']['exchange'], 
                routing_key=routing_key, 
                body=json.dumps({
                    'plate_number': detected_plate_number,
                    'is_stolen': False
                })
            )
        
        cursor.close()
        connection.close()

channel.basic_consume(
    queue=config['plate_number_character_detector_service']['routing_key']['detected_plate_number'], 
    on_message_callback=callback, 
    auto_ack=True
)

channel.start_consuming()