import requests
import time


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


def queue_image_for_odlc(image_png, stop_event):
    while not stop_event.is_set():
        response = requests.post(
            'http://localhost:8003/odlc', data={'image': image_png})
        if response.status_code == 200:
            print('Image queued')
        time.sleep(0.25)


def update_telemetry(altitude, latitude, longitude, heading):
    response = requests.post('http://localhost:8003/telemetry',
                             json={'altitude': altitude, 'latitude': latitude,
                                   'longitude': longitude, 'heading': heading})
    if response.status_code == 200:
        print("Telemetry updated")


def update_targets(type, shape_color, text_color, text, shape):
    response = requests.post('http://localhost:8003/targets',
                             json={'type': type,
                                   'class': {'shape-color': shape_color,
                                             'text-color': text_color,
                                             'text': text,
                                             'shape': shape}})
    if response.status_code == 200:
        print("Targets updated")


def get_status():
    response = requests.get('http://localhost:8003/status')
    if response.status_code == 200:
        status = response.json()
        print("Got status")
    return status
