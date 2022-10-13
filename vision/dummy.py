"""
Dummy file for SUAS Vision subsystem server
"""

import math
import random
import json

from flask import Flask, Response, request, jsonify
import redis

app = Flask(__name__)             # pylint: disable=invalid-name
r = redis.Redis(host='redis', port=6379, db=0)


@app.route('/odlc', methods=['GET'])
def get_best_object_detections():
    top_detections = []
    targets = json.loads(r.get('targets'))
    print(targets)
    i = 2
    for target in targets:
        target['count'] = i
        target['coordinates'] = [38.31+random.uniform(0.003, 0.008),
                                 -77.54+random.uniform(0.003, 0.008)]
        target['stdev'] = [random.uniform(0.0, 0.1), random.uniform(0.0, 0.1)]
        i += 1
        if target['type'] == 'alphanumeric':
            target['class']['confidence'] = math.atan(i / len(targets)) * 100
        top_detections.append(target)
    json_detections = jsonify(top_detections)
    return json_detections


# We don't care about any of the POST methods (all return empty response)
@app.route('/odlc', methods=['POST'])
def queue_image_for_odlc():
    return Response(status=200)


@app.route('/telemetry', methods=['POST'])
def update_telemetry():
    return Response(status=200)


@app.route('/targets', methods=['POST'])
def update_targets():
    target_json = json.dumps(request.get_json())
    r.set('targets', target_json)
    print(target_json)
    return Response(status=200)
