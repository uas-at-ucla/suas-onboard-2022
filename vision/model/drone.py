"""
Minimal wrapper class for Drone telemetry model and closely related methods
"""
import json

import redis

r = redis.Redis(host='redis', port=6379, db=0)


def update_telemetry(telemetry):
    """TODO: Rest of the telemetry here"""
    r.set('drone/telemetry', json.dumps(telemetry))


def get_telemetry():
    return json.loads(r.get('drone/telemetry').decode('utf-8'))
