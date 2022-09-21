"""
Minimal wrapper class for Drone telemetry model and closely related methods
"""

import redis

r = redis.Redis(host='redis', port=6379, db=0)


def update_telemetry(self, telemetry):
    """TODO: Rest of the telemetry here"""
    r.set('drone/altitude', telemetry['altitude'])


def get_altitude(self):
    return r.get('drone/altitude')
