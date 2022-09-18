from flask import Flask, Response, request, jsonify
from model.drone import Drone
from odlc.detector import Detector
from datetime import date
import cv2
import os

'''

Driver file for SUAS Vision subsystem server

'''

app = Flask(__name__)
FILE_PATH = './images/'

_drone = Drone()
_detector = Detector()

# Hello world default request
# TODO: remove this once enough people are onboarded
@app.route('/')
@app.route('/index')
def index():
    return 'Hello world!\n'

# Get most certain object detections
@app.route('/odlc', methods=['GET'])
def get_best_object_detections():
    top_detections = _detector.get_top_detections()
    json_detections = jsonify()
    print(top_detections)
    return json_detections

# Queue image POST request
@app.route('/odlc', methods=['POST'])
def queue_image_for_odlc():
    # Save file locally, so we can process it using OpenCV
    raw_data = request.get_data()
    date_str = date.today().strftime("%d-%m-%y-%h-%m-%s")
    file_location = f'{FILE_PATH}/{date_str}'
    file = open(file_location, 'wb')
    file.write(raw_data)

    # Load file and process
    try:
        img = cv2.imread(file_location, cv2.IMREAD_UNCHANGED)
        _detector.process_queued_image(img)
    except Exception as e:
        print(e)
        return 'Invalid file', 400

    # Delete file and return
    os.remove(file_location)
    return Response(status = 200)

# Update telemetry POST request
@app.route('/telemetry', methods=['POST'])
def update_telemetry():
    # Push updates to drone telemetry
    # If any info is missing, throw an error
    try:
        _drone.update_telemetry(request.json)
        print(request.json)
    except Exception as e:
        print(e)
        return 'Badly formed telemetry update', 400

    # Return empty response for success (check status code for semantics)
    return Response(status = 200)