import time
from dronekit import VehicleMode


def arm(vehicle):
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
