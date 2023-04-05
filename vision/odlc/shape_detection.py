import os
import time
import math
import struct
import json

import cv2
import numpy as np
import redis
from PIL import Image, ImageFilter

import util
from odlc.segmentation import get_text_and_shape_mask

r = redis.Redis(host='redis', port=6379, db=0)
granularity = int(os.environ.get('POLAR_SHAPE_GRANULARITY'))
CONVEX_THRESHOLD = float(os.environ.get('CONCAVE_SHAPE_AREA_RATIO_THRESHOLD'))


def interpolate(i, dist):
    j = i
    while j >= 0 and dist[j]['count'] == 0:
        j -= 1
    k = i
    while k < len(dist) and dist[k]['count'] == 0:
        k += 1

    if j >= 0 and k < len(dist):
        return ((i-j) * dist[k]['dist'] / dist[k]['count'] +
                (k-i) * dist[j]['count'] / dist[j]['count']) / (k-j)
    elif j >= 0:
        return dist[j]['count']
    elif k < len(dist):
        return dist[k]['count']


def confidence_mapping(c):
    if c <= 0.90:
        return 2.0**(20 * c - 19)
    else:
        return 1.1668 + 0.0724 * np.log(c - 0.90)


def initialize(targets):
    r.set('vision/shapes', json.dumps(targets))
    for comp in targets:
        cdata = []
        with open(f"/app/odlc/shape_reference/{comp}.txt") as fp:
            for line in fp:
                x = line[:-1]
                cdata.append(float(x))
        cdata = cdata[0:granularity]
        buf = struct.pack('%sf' % len(cdata), *cdata)
        r.set(f"vision/shape-data/{comp}", buf)


def detect_shape(img):

    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    _, masked_shape = get_text_and_shape_mask(img)

    # Erode mask
    kernel = np.ones((3, 3), np.uint8)
    masked_shape = cv2.erode(masked_shape, kernel)

    # Clean up edges with PIL ModeFilter
    filtered = Image.fromarray(masked_shape)
    filtered = filtered.filter(ImageFilter.ModeFilter(size=9))
    masked_shape = np.array(filtered)

    # Fill in the shape
    cnts, _ = cv2.findContours(masked_shape, cv2.RETR_TREE,
                               cv2.CHAIN_APPROX_SIMPLE)
    largest = max(cnts, key=cv2.contourArea)

    masked_shape = cv2.drawContours(np.zeros(img.shape[0:2]),
                                    [largest], 0, 255, -1)
    hull = cv2.drawContours(np.zeros(img.shape[0:2]),
                            [cv2.convexHull(largest, False)], 0, 255, -1)

    # Get the shape outline
    edges = cv2.Canny(np.uint8(masked_shape), 100, 200)
    edge_hull = cv2.Canny(np.uint8(hull), 100, 200)

    util.debug_imwrite(edges,
                       f"./images/debug/img-edges-{time.time()}.png")
    util.debug_imwrite(edge_hull,
                       f"./images/debug/img-hull-{time.time()}.png")

    # Determine if the shape is concave
    M = cv2.moments(edge_hull)
    M_comp = cv2.moments(edges)
    concave = M["m00"] / M_comp["m00"] < CONVEX_THRESHOLD

    if M["m00"] == 0:  # No contour exists, so we can't detect anything
        return []
    cX = round(M["m10"] / M["m00"])
    cY = round(M["m01"] / M["m00"])

    # Convert contour outline to polar form
    dist = [{'count': 0, 'dist': 0} for i in range(granularity + 1)]
    tot = 0
    count = 0
    h, w, d = img.shape
    for y in range(0, h):
        for x in range(0, w):
            if edge_hull[y, x] != 0:
                dx = x - cX
                dy = y - cY
                angle = math.atan2(dy, dx)
                d = math.sqrt(dx*dx + dy*dy)
                slot = int((angle + math.pi) / 2 / math.pi * granularity)
                dist[slot]['count'] += 1
                dist[slot]['dist'] += d
                tot += d
                count += 1

    # Normalize polar edge values relative to mean radius
    mdist = tot / count
    data = []
    for i in range(len(dist)):
        entry = dist[i]
        if entry['count'] != 0:
            data.append(entry['dist'] / entry['count'] / mdist)
        else:
            data.append(interpolate(i, dist) / mdist)

    # Duplicate data and truncate last entry to allow for processing as
    # periodic signal
    dr = data[0:granularity] + data[0:granularity]

    # Perform comparison process
    predictions = []
    targets = json.loads(r.get('vision/shapes').decode('utf-8'))
    for comp in targets:
        buf = r.get(f"vision/shape-data/{comp}")
        cdata = struct.unpack('%sf' % granularity, buf)
        miou = 0

        # Similar to correlation/convolution integral, but instead evaluating
        # Jaccard IOU metric for each possible delay
        for i in range(granularity):
            intersection = 0
            union = 0
            for j in range(granularity):
                intersection += min(cdata[j], dr[i+j])
                union += max(cdata[j], dr[i+j])
            if (intersection / union) > miou:
                miou = intersection / union
        predictions.append((comp, confidence_mapping(miou)))
    predictions.sort(key=lambda x: -1.0 * x[1])

    # Concave, so pentagon ==> star and octagon ==> cross
    if concave:
        sc = next(p for p in predictions if p[0] == 'pentagon')[1]
        cc = next(p for p in predictions if p[0] == 'octagon')[1]
        p = [('star', sc), ('cross', cc)]
        p.sort(key=lambda x: -1.0 * x[1])
        return p

    return predictions


# Helper method for generating reference data used to compare shapes with
def generate_reference_data(names):
    for name in names:
        img = cv2.cvtColor(cv2.imread(f"/app/odlc/shape_reference/{name}.png"),
                           cv2.COLOR_BGR2GRAY)

        edges = cv2.Canny(np.uint8(img), 100, 200)

        M = cv2.moments(edges)
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])

        dist = [{'count': 0, 'dist': 0} for i in range(101)]
        tot = 0
        count = 0
        h, w = img.shape
        for y in range(0, h):
            for x in range(0, w):
                if edges[y, x] != 0:
                    dx = x - cX
                    dy = y - cY
                    angle = math.atan2(dy, dx)
                    d = math.sqrt(dx*dx + dy*dy)
                    slot = int((angle + math.pi) / 2 / math.pi * 100)
                    dist[slot]['count'] += 1
                    dist[slot]['dist'] += d
                    tot += d
                    count += 1

        mdist = tot / count

        data = []
        for i in range(len(dist)):
            entry = dist[i]
            if entry['count'] != 0:
                data.append(entry['dist'] / entry['count'] / mdist)
            else:
                data.append(interpolate(i, dist) / mdist)

        with open(f"/app/odlc/shape_reference/{name}.txt", 'w') as fp:
            for item in data:
                fp.write("%s\n" % item)
