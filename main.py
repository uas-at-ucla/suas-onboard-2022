"""
Driver file for SUAS Vision subsystem server
"""

from datetime import date
import os

from flask import Flask, Response, request, jsonify
import cv2

from model.drone import Drone
from odlc.detector import Detector


app = Flask(__name__)             # pylint: disable=invalid-name
FILE_PATH = './images/'

_drone = Drone()                  # pylint: disable=invalid-name
_detector = Detector()            # pylint: disable=invalid-name


@app.route('/')
@app.route('/index')
def index():
    """
    Hello world default request
    TODO: remove this once enough people are onboarded
    """
    return 'Hello world!\n'


@app.route('/odlc', methods=['GET'])
def get_best_object_detections():
    """
    Get most certain object detections
    """
    top_detections = _detector.get_top_detections()
    json_detections = jsonify()
    print(top_detections)
    return json_detections


@app.route('/odlc', methods=['POST'])
def queue_image_for_odlc():
    """
    Queue image POST request
    """
    # Save file locally, so we can process it using OpenCV
    raw_data = request.get_data()
    date_str = date.today().strftime("%d-%m-%y-%h-%m-%s")
    file_location = f'{FILE_PATH}/{date_str}'
    with open(file_location, 'wb') as file:
        file.write(raw_data)

        # Load file and process
        try:
            img = cv2.imread(file_location, cv2.IMREAD_UNCHANGED)
            _detector.process_queued_image(img)
        except Exception as exc:  # pylint: disable=broad-except
            print(repr(exc))
            if os.environ.get('DEBUG'):
                return 'Exception thrown, see server logs', 500
            return 'Invalid file', 400

    # Delete file and return
    os.remove(file_location)
    return Response(status=200)


@app.route('/telemetry', methods=['POST'])
def update_telemetry():
    """
    Update telemetry POST request
    """
    # Push updates to drone telemetry
    # If any info is missing, throw an error
    try:
        _drone.update_telemetry(request.json)
        print(request.json)
    except KeyError as exc:
        print(repr(exc))
        return 'Badly formed telemetry update', 400

    # Return empty response for success (check status code for semantics)
    return Response(status=200)
