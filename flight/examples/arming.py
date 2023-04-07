from __future__ import print_function
import time
from dronekit import connect, VehicleMode

import argparse
parser = argparse.ArgumentParser(
    description='Commands vehicle using vehicle.simple_goto.')
parser.add_argument('--connect',
                    help="Vehicle connection target string. If not specified, \
                    SITL automatically started and used.")
args = parser.parse_args()

connection_string = args.connect
sitl = None


# Start SITL if no connection string specified
if not connection_string:
    import dronekit_sitl
    sitl = dronekit_sitl.start_default()
    connection_string = sitl.connection_string()


# Connect to the Vehicle
print('Connecting to vehicle on: %s' % connection_string)
vehicle = connect(connection_string, wait_ready=True)


def arm_and_takeoff(aTargetAltitude):

    # pre-arm checks:
    print("performing pre-arm checks:")

    while vehicle.gps_0.fix_type < 2 and vehicle.gps_0.fix_type is not None:
        print("Waiting for GPS...:", vehicle.gps_0.fix_type)
        time.sleep(1)

    while vehicle.battery.level < 20:
        print("Battery level too low...:", vehicle.battery.level)
        time.sleep(1)

    while not vehicle.ekf_ok:
        print("EKF not acceptable...")
        time.sleep(1)

    while not vehicle.is_armable:
        print(" Waiting for vehicle to initialise...")
        time.sleep(1)

    print("Arming motors")

    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

    while not vehicle.armed:
        print(" Waiting for arming...")
        time.sleep(1)

    print("Taking off!")
    vehicle.simple_takeoff(aTargetAltitude)

    while True:
        print(" Altitude: ", vehicle.location.global_relative_frame.alt)
        # Break and return from function just below target altitude.
        if vehicle.location.global_relative_frame.alt \
                >= aTargetAltitude * 0.95:
            print("Reached target altitude")
            break
        time.sleep(1)
