from flask import Flask, Response, request, jsonify
from model.drone import Drone
from datetime import date
import cv2
import os

app = Flask(__name__)
FILE_PATH = './images/'

_drone = Drone()
_detections = {}
_top_detections = {}

# Hello world default request
@app.route('/')
@app.route('/index')
def index():
    return 'Hello world!\n'

# Get most certain object detections
@app.route('/odlc', methods=['GET'])
def get_best_object_detections():
    json_detections = jsonify(_top_detections)
    print(_top_detections)
    return json_detections

# Main routine for processing the image (however we decide to)
def process_queued_image(img):
    # TODO: process the image
    print(img.shape)

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
        process_queued_image(img)
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
        _drone.update_telemetry(request.json['altitude'])
        # TODO: Put remaining drone telemetry here...
    except Exception as e:
        print(e)
        return 'Badly formed telemetry update', 400

    # Return empty response for success (check status code for semantics)
    return Response(status = 200)