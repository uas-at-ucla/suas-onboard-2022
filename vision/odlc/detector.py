
"""
Stateful representation of vision subsystem
"""

import os
import math
import json

import cv2
import redis
import numpy as np

import log
from odlc import inference, color_detection, gps, tesseract, shape_detection

r = redis.Redis(host='redis', port=6379, db=0)
tolerance = float(os.environ.get('DETECTION_TOLERANCE'))
alphanumeric_model = inference.Model('/app/odlc/models/alphanumeric_model.pth')
emergent_model = inference.Model('/app/odlc/models/emergent_model.pth')
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


def compute_alphanumeric_similarity(target, detection):
    if target['type'] == 'dummy' or detection['type'] == 'dummy':
        return 0

    similarity = 0

    for c in ['shape', 'text', 'shape-color', 'text-color']:
        if target['class'][c] in detection['class'][c].keys():
            items = [(s, c) for s, c in detection['class'][c].items()]
            items.sort(key=lambda x: x[1], reverse=True)
            ind = [i for i in range(len(items)) if items[i][0] ==
                   target['class'][c]][0]
            conf = 1
            if c == 'shape':
                conf = items[ind][1]
            elif c == 'text':
                conf = items[ind][1] / 100.0
            else:
                conf = items[ind][1] / detection['count']
            if ind != -1:
                similarity += 0.25 * np.exp(-0.7 * ind) * conf

    return similarity


def bad_pairing_found(similarity_matrix, pairings):
    n = len(pairings)
    for i in range(n):
        for j in range(n):
            base_stability = similarity_matrix[i][pairings[i]] + \
                             similarity_matrix[j][pairings[j]]
            new_stability = similarity_matrix[j][pairings[i]] + \
                similarity_matrix[i][pairings[j]]
            if new_stability > base_stability:
                temp = pairings[i]
                pairings[i] = pairings[j]
                pairings[j] = temp
                return True
    return False


def update_targets(targets):
    target_json = json.dumps(targets)
    alphanumeric_targets = [target['class']['shape'] for target in
                            targets if target['type'] == 'alphanumeric']
    num_emergent = sum(t['type'] == 'emergent' for t in targets)
    r.set('detector/num_emergent', num_emergent)
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
    emergent_detections = emergent_model.detect_boxes(img)
    log.info(f"Emergent detections: {len(emergent_detections)}")
    for i in range(len(emergent_detections)):
        dbox = emergent_detections[i]
        lat, lon = gps.tag(telemetry['altitude'], telemetry['latitude'],
                           telemetry['longitude'], telemetry['heading'],
                           float(os.environ.get('CAMERA_SENSOR_WIDTH')),
                           float(os.environ.get('CAMERA_FOCAL_LENGTH')),
                           img.shape[0], img.shape[1],
                           int(dbox[0]) + int(dbox[2]) / 2.0,
                           int(dbox[1]) + int(dbox[3]) / 2.0,
                           False)

        detection = {
            'type': 'emergent',
            'coords': [math.degrees(lat), math.degrees(lon)],
        }

        # Find most similar existing detection
        min_diff = float('inf')
        min_comp = {}
        for comp in detections:
            diff = get_detection_diff(comp, detection)
            if diff < min_diff:
                min_diff = diff
                min_comp = comp

        # Duplicate found
        if min_diff < tolerance:
            log.info('Duplicate detected, updating duplicate')
            ccount = min_comp['count']
            min_comp['coords'][0] = (lat + min_comp['coords'][0] * ccount) \
                / (1 + ccount)
            min_comp['coords'][1] = (lon + min_comp['coords'][1] * ccount) \
                / (1 + ccount)

            if debugging:
                log.info(min_comp)
        else:
            print('New detection found')
            detection['count'] = 1
            if debugging:
                log.info(detection)
            detections.append(detection)

    # Get alphanumeric detections
    alphanumeric_detections = alphanumeric_model.detect_boxes(img)
    log.info(f"Alphanumeric detections: {len(alphanumeric_detections)}")
    for i in range(len(alphanumeric_detections)):
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
            'coords': [math.degrees(lat), math.degrees(lon)],
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
    # Load detections and intended targets
    detections = json.loads(r.get('detector/detections'))

    if debugging:
        log.info(detections)

    targets = json.loads(r.get('detector/targets'))
    num_emergent = int(r.get('detector/num_emergent'))
    ret = []

    # Find best emergent detections
    emergent_detections = [d for d in detections if d['type'] == 'emergent']
    emergent_detections.sort(key=lambda x: -1.0 * get_detection_confidence(x))
    for i in range(min(num_emergent, len(emergent_detections))):
        ret.append(emergent_detections[i])

    # Find matches between targets and detections using stable matching
    # algorithm. Note that we aren't guaranteed to have the same number of
    # alphanumeric targets and detections, so we have to pad whichever side
    # has fewer with dummy entries that have 0 similarity with any other
    # target/detection
    alpha_detections = [d for d in detections if d['type'] == 'alphanumeric']
    alpha_targets = [t for t in targets if t['type'] == 'alphanumeric']
    n = max(len(alpha_targets), len(alpha_detections))
    if len(alpha_detections) < n:
        for i in range(n - len(alpha_detections)):
            alpha_detections.append({'type': 'dummy'})

    if len(alpha_targets) < n:
        for i in range(n - len(alpha_targets)):
            alpha_targets.append({'type': 'dummy'})

    # Compute preferences
    similarity_matrix = [[compute_alphanumeric_similarity(alpha_targets[i],
                          alpha_detections[j]) for j in range(n)]
                         for i in range(n)]

    pairings = [i for i in range(n)]
    bad_found = bad_pairing_found(similarity_matrix, pairings)
    while bad_found:
        bad_found = bad_pairing_found(similarity_matrix, pairings)

    for i in range(n):
        if alpha_targets[i]['type'] != 'dummy' and \
           alpha_detections[pairings[i]]['type'] != 'dummy':
            alpha_targets[i]['coords'] = \
                alpha_detections[pairings[i]]['coords']
            ret.append(alpha_targets[i])

    if debugging:
        log.info(ret)

    return ret
