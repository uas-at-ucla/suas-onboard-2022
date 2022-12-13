
"""
Stateful representation of vision subsystem
"""

import os
import math
import json

import cv2

import redis

import log
from odlc import inference, color_detection, gps, tesseract, shape_detection

r = redis.Redis(host='redis', port=6379, db=0)
tolerance = float(os.environ.get('DETECTION_TOLERANCE'))
alphanumeric_model = inference.Model('/app/odlc/models/alphanumeric_model.pth')
debugging = (int(os.environ.get('DEBUG')) == 1)


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

    # Calculate difference using Haversine formula
    # Difference returned in feet
    la1, lo1 = d_1['coords']
    la2, lo2 = d_2['coords']
    dla = math.radians(abs(la1 - la2))
    dlo = math.radians(abs(lo1 - lo2))

    a = math.sin(dla / 2.0)**2 + math.cos(math.radians(la1)) * \
        math.radians(la2) * math.sin(dlo / 2.0) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return c * 2.093e7


def update_targets(targets):
    r.set('detector/num_detections', len(targets))
    target_json = json.dumps(targets)
    alphanumeric_targets = [target['class']['shape'] for target in
                            targets if target['type'] == 'alphanumeric']
    shape_detection.initialize(alphanumeric_targets)
    r.set('detector/targets', target_json)
    detection_json = json.dumps([])
    r.set('detector/detections', detection_json)


def process_queued_image(img, telemetry):
    """
    Main routine for image processing
    """
    global alphanumeric_model

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
            log.info('Duplicate detected:')
            print(min_comp)
            print(detection)

            # What happens when duplicate detected
            # Update min_comp count, weighted average, stdev, etc.
        else:
            print('New detection found')
            print(detection)
            detections.append(detection)

    # Get alphanumeric detections
    alphanumeric_detections = alphanumeric_model.detect_boxes(img)
    log.info(f"Alphanumeric detections: {alphanumeric_detections.shape[0]}")
    for i in range(alphanumeric_detections.shape[0]):
        # Crop image and write out image to debug output
        # Resize the cropped image with interpolation to hopefully give
        # better results for classification
        dbox = alphanumeric_detections[i]
        crop_img = img[int(dbox[1]):int(dbox[3]), int(dbox[0]):int(dbox[2])]
        # Save the preprocessed image if we are debugging
        if debugging:
            cv2.imwrite(f"./images/debug/img-crop-{i}.png", crop_img)

        # Get classification info
        fc, bc = color_detection.get_text_and_shape_color(crop_img)
        text = tesseract.get_matching_text(crop_img)
        shapes = shape_detection.detect_shape(crop_img)
        lat, lon = gps.tag(telemetry['altitude'], telemetry['latitude'],
                           telemetry['longitude'], telemetry['heading'],
                           float(os.environ.get('CAMERA_SENSOR_WIDTH')),
                           float(os.environ.get('CAMERA_FOCAL_LENGTH')),
                           img.shape[0], img.shape[1],
                           int(dbox[0]) + int(dbox[2]) / 2.0,
                           int(dbox[1]) + int(dbox[3]) / 2.0,
                           False)

        d = {
            'type': 'alphanumeric',
            'coords': [lat, lon],
        }

        # Find most similar existing detection
        min_diff = float('inf')
        min_comp = {}
        for comp in detections:
            diff = get_detection_diff(comp, d)
            if diff < min_diff:
                min_diff = diff
                min_comp = comp

        # If they are similar enough, combine detections, otherwise
        # add the new detection to the detection list
        if min_diff < tolerance:
            log.info('Duplicate detected, updating duplicate')
            ccount = min_comp['count']
            min_comp['coords'][0] = (lat + min_comp['coords'][0] * ccount) \
                / (1 + ccount)
            min_comp['coords'][1] = (lon + min_comp['coords'][1] * ccount) \
                / (1 + ccount)
            min_comp['count'] = 1 + ccount
            min_comp['class']['text-color'][fc] = \
                min_comp['class']['text-color'].get(fc, 0) + 1
            min_comp['class']['shape-color'][fc] = \
                min_comp['class']['shape-color'].get(bc, 0) + 1
            for s, conf in shapes:
                min_comp['class']['shape'][s] = \
                    min_comp['class']['shape'].get(s, 0) + conf
            for t, conf in text:
                min_comp['class']['text'][str(t)] = \
                    min_comp['class']['text'].get(str(t), 0) + int(conf)

            if debugging:
                log.info(min_comp)

            # What happens when duplicate detected
            # Update min_comp count, weighted average, stdev, etc.
        else:
            log.info('New detection found')
            d['count'] = 1
            d['class'] = {
                'text-color': {fc: 1},
                'shape-color': {bc: 1},
                'shape': {},
                'text': {},
            }
            for s, conf in shapes:
                d['class']['shape'][s] = conf
            for t, conf in text:
                d['class']['text'][str(t)] = int(conf)

            if debugging:
                log.info(d)

            detections.append(d)

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
