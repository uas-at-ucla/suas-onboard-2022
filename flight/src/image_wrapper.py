import requests
import json
import time
import os
import multiprocessing

def index():
    response = requests.get('http://localhost:8003/index')
    if response.status_code == 200:
        index = response.json()
        print("Got index")
    return index


def get_best_object_detections():
    response = requests.get('http://localhost:8003/odlc')
    if response.status_code == 200:
        detections = response.json()
        print("Got object detections")
    return detections


def queue_image_for_odlc(data):
    response = requests.post("http://localhost:8003/odlc",
                             data=data,
                             headers={'Content-Type':
                                      'application/octet-stream'})
    if response.status_code == 200:
        print('Image queued')

def update_telemetry(altitude, latitude, longitude, heading):
    response = requests.post('http://localhost:8003/telemetry',
                             json={'altitude': altitude, 'latitude': latitude,
                                   'longitude': longitude, 'heading': heading})
    if response.status_code == 200:
        print("Telemetry updated")


def update_targets(root_dir):
    with open(os.path.join(root_dir, 'targets.json'), 'r') as tjf:
        target_json = json.loads(tjf.read())
    response = requests.post('http://localhost:8003/targets',
                             json=target_json)
    if response.status_code == 200:
        print("Targets updated")


def get_status():
    response = requests.get('http://localhost:8003/status')
    if response.status_code == 200:
        status = response.json()
        print("Got status")
    return status

def update_images(cam):
    while True:
        fp = cam.take_picture()
        if fp != None:
            with open(fp, 'rb') as im:
                data = im.read()
                queue_image_for_odlc(data)
            os.remove(fp)
