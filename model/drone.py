"""
Minimal wrapper class for Drone telemetry model and closely related methods
"""


class Drone:
    """Drone class"""
    def __init__(self):
        """Initialize drone state"""
        self.altitude = 0

    def update_telemetry(self, telemetry):
        """TODO: Rest of the telemetry here"""
        self.altitude = telemetry['altitude']

    def get_altitude(self):
        """Accessor for altitude"""
        return self.altitude
