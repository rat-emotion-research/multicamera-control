from flask import Flask, request, jsonify

app = Flask(__name__)

sensors = [
    # "192.168.0.32:5000",
    # "192.168.0.33:5000",
    # "192.168.0.34:5000"
    "pi1.local:5000",
    "pi2.local:5000",
    "pi4.local:5000"
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