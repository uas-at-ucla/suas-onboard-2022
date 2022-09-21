
"""
Stateful representation of vision subsystem
"""

import os
import math
import json

import redis

from odlc import inference

r = redis.Redis(host='redis', port=6379, db=0)
tolerance = int(os.environ.get('DETECTION_TOLERANCE'))


def get_detection_confidence(detection):
    """
    Assign numerical value to the confidence we have in a detection
    Currently only considers the number of times it has been detected
    Potential ideas: location stdev
    """
    return detection['count']


def get_detection_diff(d_1, d_2):
    """
    Determine if two detections are different
    Currently considers detection type and whether the distance between
    coordinates is within our allowed tolerance
    """
    if d_1['type'] != d_2['type']:
        return float('inf')

    # Convert bounding boxes to vectors and calculate Euclidean distance
    b_1 = d_1['coords']
    b_2 = d_2['coords']
    dist = math.sqrt(((b_1[0]-b_2[0]) ** 2) + ((b_1[1]-b_2[1]) ** 2))

    return dist


def update_targets(targets):
    r.set('detector/num_detections', len(targets))
    target_json = json.dumps(targets)
    r.set('detector/targets', target_json)
    detection_json = json.dumps([])
    r.set('detector/detections', detection_json)


def process_queued_image(img):
    """
    Main routine for image processing
    """
    detections = json.loads(r.get('detector/detections'))

    # Get emergent detections
    emergent_detections = inference.detect_mannikins(img)
    for detection in emergent_detections:
        # Find most similar existing detection
        min_diff = float('inf')
        min_comp = {}
        for comp in detections:
            diff = get_detection_diff(comp, detection)
            if diff < min_diff:
                min_diff = diff
                min_comp = comp

        # If they are similar enough, combine detections, otherwise
        # add the new detection to the detection list
        if min_diff < tolerance:
            print('Duplicate detected:')
            print(min_comp)
            print(detection)

            # What happens when duplicate detected
            # Update min_comp count, weighted average, stdev, etc.
        else:
            print('New detection found')
            print(detection)
            detections.append(detection)

    json_detections = json.dumps(detections)
    r.set('detector/detections', json_detections)


def get_top_detections():
    """
    Returns the top N detections we are most confident in
    """
    # If not enough detections, return everything we have so far
    detections = json.loads(r.get('detector/detections'))
    num_detections = int(r.get('detector/num_detections'))
    if len(detections) <= num_detections:
        return detections

    # Sort detections increasing by confidence and return
    detections.sort(key=lambda x: -1.0 * get_detection_confidence(x))
    return detections[0:num_detections]
