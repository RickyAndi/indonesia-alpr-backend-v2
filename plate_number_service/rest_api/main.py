import datetime

from mysql import connector
from flask import Flask, json, jsonify, request

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

app = Flask(__name__)

@app.route('/stolen-plates', methods=['GET'])
def get_list_of_stolen_plate():

    try:
        
        cursor.execute("SELECT id, plate_number FROM stolen_plates")
        stolen_plates = cursor.fetchall()
        
        return app.response_class(
            response=json.dumps(stolen_plates),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:

        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=500,
            mimetype='application/json'
        )

@app.route('/stolen-plate', methods=['GET'])
def check_if_plate_is_stolen():
    
    plate_number = request.args.get('plate_number')
    
    if plate_number is None:
        return app.response_class(
            response=json.dumps({'message': 'Please provide plate number'}),
            status=400,
            mimetype='application/json'
        )

    try:
        cursor.execute("SELECT id FROM stolen_plates WHERE id = %s", (plate_number,))
        stolen_plates = cursor.fetchall()

        if len(stolen_plates) == 0:
            return app.response_class(
                response=json.dumps({'stolen': False}),
                status=200,
                mimetype='application/json'
            )  
        
        return app.response_class(
            response=json.dumps({'stolen': True}),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:

        return app.response_class(
            response=json.dumps({'message': str(e)}),
            status=500,
            mimetype='application/json'
        )
    

@app.route('/stolen-plate', methods=['POST'])
def add_stolen_plate():
    
    try:
        cursor = connection.cursor(prepared=True)
        sql = "INSERT INTO stolen_plates (plate_number) VALUES (%s)"
        values = (request.json.get("plate_number"),)
        mycursor.execute(sql, values)
        
        return app.response_class(
            response=json.dumps({"message": "stolen plate has been added"}),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:

        return app.response_class(
            response=json.dumps({"message": e.message}),
            status=500,
            mimetype='application/json'
        )

@app.route('/stolen-plate/<stolen_plate_id>', methods=['PUT'])
def update_stolen_plate(stolen_plate_id=None):

    if stolen_plate_id is None:
        return app.response_class(
            response=json.dumps({"message": "Please provide the stolen plate id"}),
            status=400,
            mimetype='application/json'
        )

    try:
        cursor = connection.cursor(prepared=True)
        sql = "UPDATE stolen_plates SET plate_number = %s WHERE id = %s"
        values = (request.json.get("plate_number"), stolen_plate_id)
        mycursor.execute(sql, values)
        
        return app.response_class(
            response=json.dumps({"message": "stolen plate has been updated"}),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        
        return app.response_class(
            response=json.dumps({"message": e.message}),
            status=500,
            mimetype='application/json'
        )

@app.route(('/stolen-plate/<stolen_plate_id>', methods=['DELETE']))
def delete_stolen_plate():

    if stolen_plate_id is None:
        return app.response_class(
            response=json.dumps({"message": "Please provide the stolen plate id"}),
            status=400,
            mimetype='application/json'
        )

    try:
        cursor = connection.cursor(prepared=True)
        sql = "DELETE stolen_plates WHERE id = %s"
        values = (stolen_plate_id,)
        mycursor.execute(sql, values)
        
        return app.response_class(
            response=json.dumps({"message": "stolen plate has been deleted"}),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:
        
        return app.response_class(
            response=json.dumps({"message": str(e)}),
            status=500,
            mimetype='application/json'
        )

@app.route('/stolen-plates/detected', methods=['GET'])
def get_list_of_detected_stolen_plate():
    try:
        
        date = request.args.get('date')
        if date is None:
            date = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

        sql = "SELECT sp.plate_number, dsp.detected_date FROM detected_stolen_plates dsp JOIN stolen_plates sp ON dsp.stolen_plate_id = sp.id WHERE dsp.detected_time = %s"
        cursor = connection.cursor(prepared=True)
        cursor.execute(sql, (date,))

        detected_stolen_plates = cursor.fetchall()
        return app.response_class(
            response=json.dumps(detected_stolen_plates),
            status=200,
            mimetype='application/json'
        )

    except Exception as e:

        return app.response_class(
            response=json.dumps({"message": str(e)}),
            status=500,
            mimetype='application/json'
        )

app.run(host='0.0.0.0', port=config['plate_number_service']['rest_server']['port'])