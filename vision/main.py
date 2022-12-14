"""
Driver file for SUAS Vision subsystem server
"""

from queue import Queue
from threading import Thread
import os
import time
import traceback
import math

from flask import Flask, Response, request, jsonify, send_from_directory
import cv2
import redis

import model.drone as drone
import odlc.detector as detector
import util as util


app = Flask(__name__)             # pylint: disable=invalid-name
image_queue = Queue()
FILE_PATH = './images/'
r = redis.Redis(host='redis', port=6379, db=0)


@app.route('/')
@app.route('/index')
def index():
    return send_from_directory('html', 'index.html')


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
    file_location = f'{FILE_PATH}/{time.time_ns()}-'
    with open(file_location, 'wb') as file:
        file.write(raw_data)
        image_queue.put({"file_location": file_location,
                         "telemetry": drone.get_telemetry()})

    return Response(status=200)


def process_image_queue(queue):
    util.info('Queue processing thread starting')
    while True:
        task = queue.get()
        file_location = task['file_location']
        telemetry = task['telemetry']
        print('Processing queued image')
        start_time = time.time()

        # Load file and process
        try:
            img = cv2.imread(file_location, cv2.IMREAD_UNCHANGED)
            detector.process_queued_image(img, telemetry)
        except Exception:  # pylint: disable=broad-except
            traceback.print_exc()

        # Delete file and return
        os.remove(file_location)
        queue.task_done()
        util.info('Queued image processed')
        r.incr('vision/images_processed')
        r.incrbyfloat('vision/active_time', time.time() - start_time)


@app.route('/telemetry', methods=['POST'])
def update_telemetry():
    """
    Update telemetry POST request
    """

    # Push updates to drone telemetry
    # If any info is missing, throw an error
    try:
        req = request.json
        assert 'altitude' in req
        assert 'latitude' in req
        assert 'longitude' in req
        assert 'heading' in req
        req['latitude'] = math.radians(req['latitude'])
        req['longitude'] = math.radians(req['longitude'])
        drone.update_telemetry(req)
    except Exception as exc:
        util.error(repr(exc))
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
    except Exception as exc:
        util.error(repr(exc))
        return 'Badly formed target update', 400

    # Return empty response for success (check status code for semantics)
    return Response(status=200)


@app.route('/status', methods=['GET'])
def get_status():
    """
    Get queue status GET request
    """
    num_processed = int(r.get('vision/images_processed').decode('utf-8'))
    if num_processed > 0:
        tpi = float(r.get('vision/active_time').
                    decode('utf-8')) / num_processed
    else:
        tpi = 0.0
    status = {
        'processed_images': num_processed,
        'queued_images': image_queue.qsize(),
        'time_per_image': tpi
    }

    return jsonify(status)


worker = Thread(target=process_image_queue, args=(image_queue, ))
worker.setDaemon(True)
worker.start()

r.set('vision/images_processed', 0)
r.set('vision/active_time', 0.0)
