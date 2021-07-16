from flask import Flask, request, jsonify

app = Flask(__name__)

sensors = [
    "192.168.0.32",
    "192.168.0.33",
    "192.168.0.34"
]

@app.route('/sensors')
def handle_sensors():
    if request.method == 'GET':
        return jsonify(sensors)
    elif request.method == 'PUT':
        sensors.append(request.data)
    
@app.route('/sensors/<sensor>')
def handle_sensor(sensor):
    if request.method == 'DELETE':
        sensor.remove(request.data)