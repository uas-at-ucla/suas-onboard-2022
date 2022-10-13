"""
Driver file for SUAS Vision subsystem server
"""

from datetime import date
import os

from flask import Flask, Response, request, jsonify
import cv2

import model.drone as drone
import odlc.detector as detector


app = Flask(__name__)             # pylint: disable=invalid-name
FILE_PATH = './images/'


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
    top_detections = detector.get_top_detections()
    json_detections = jsonify(top_detections)
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
            detector.process_queued_image(img)
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
        drone.update_telemetry(request.json)
        print(request.json)
    except Exception as exc:
        print(repr(exc))
        return 'Badly formed telemetry update', 400

    # Return empty response for success (check status code for semantics)
    return Response(status=200)


@app.route('/targets', methods=['POST'])
def update_targets():
    """
    Update target POST request
    """

    # Push updates to drone targets
    # If any info is missing, throw an error
    try:
        data_list = request.get_json()

        # Validate data, this will throw an error if anything is off
        for data in data_list:
            if data['type'] == 'emergent':
                assert len(data.keys()) == 1
            elif data['type'] == 'alphanumeric':
                assert len(data.keys()) == 2
                data_class = data['class']
                assert len(data_class) == 4
                assert type(data_class['shape-color']) == str
                assert type(data_class['text-color']) == str
                assert type(data_class['text']) == str
                assert type(data_class['shape']) == str
            else:
                raise Exception('Type not recognized')

        detector.update_targets(data_list)
        print(request.json)
    except Exception as exc:
        print(repr(exc))
        return 'Badly formed target update', 400

    # Return empty response for success (check status code for semantics)
    return Response(status=200)
