'''

Minimal wrapper class for Drone telemetry model and closely related methods

'''

class Drone:
    def __init__(self):
        self.altitude = 0
    
    # TODO: Rest of the telemetry here
    def update_telemetry(self, telemetry):
        self.altitude = telemetry['altitude']
    
    def get_altitude(self):
        return self.altitude

    # TODO: Rest of the telemetry accessors here