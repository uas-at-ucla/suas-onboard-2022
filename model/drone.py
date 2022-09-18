class Drone:
    def __init__(self):
        self.altitude = 0
        self.coordinates = (0, 0)
    
    # TODO: Rest of the telemetry here
    def update_telemetry(self, altitude):
        self.altitude = altitude
    
    def get_altitude(self):
        return self.altitude

    # TODO: Rest of the telemetry accessors here