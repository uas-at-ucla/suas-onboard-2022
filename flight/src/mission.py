import time

from dronekit import Command, VehicleMode
from pymavlink import mavutil

from errors import retry

# TODO: move constants
METERS_PER_FEET = 0.3048

ACC_RADIUS = 7.62  # 25 feet

CLIMB_ANGLE = 20
DESCENT_ANGLE = 20

# AIRFIELD_ALT = 43.2816  # Airfield is 142 feet MSL
AIRFIELD_ALT = 209  # Apollo airfield
MIN_RELATIVE_ALT = 22.86  # 75 feet
MAX_RELATIVE_ALT = 121.92  # 400 feet


# Puts the vehicle into flight_mode.
@retry(5)
def mode_switch(vehicle, flight_mode):
    while vehicle.mode.name != flight_mode:
        vehicle.mode = VehicleMode(flight_mode)
        print("Waiting for mode change to " + flight_mode + " . . .")
        time.sleep(1)
    print(flight_mode)


# Puts the vehicle into AUTO mode.
def start_mission(vehicle):
    mode_switch(vehicle, "AUTO")


@retry(5)
def mission_reset(vehicle, timeout=30):
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    cmds.clear()
    cmds.upload(timeout=timeout)


@retry(5)
def mission_add_takeoff(vehicle, timeout=30):
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    takeoff_command = Command(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        mavutil.mavlink.MAV_CMD_NAV_TAKEOFF,
        0, 0,
        CLIMB_ANGLE,
        0, 0, 0, 0, 0,
        MIN_RELATIVE_ALT
    )
    cmds.add(takeoff_command)
    cmds.upload(timeout=timeout)


@retry(5)
def mission_add_land(vehicle, landing_point, timeout=30):
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    land_command = Command(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        mavutil.mavlink.MAV_CMD_NAV_LAND,
        0, 0,
        0, 0, 0, 0,
        landing_point[0],
        landing_point[1],
        0
    )
    cmds.add(land_command)
    cmds.upload(timeout=timeout)


# Generate waypoints from waypoints given during competition.
# Note: Altitudes are given in feet MSL(global)
def generate_waypoint_list(filename):
    # Waypoints format: [lat, lon, alt]
    waypoint_list = []
    with open(filename) as f:
        for line in f:
            waypoint = line.strip().split(",")
            waypoint_list.append([float(coord) for coord in waypoint])

    for waypoint in waypoint_list:
        # Convert altitude to meters
        waypoint[2] *= METERS_PER_FEET
        waypoint[2] -= AIRFIELD_ALT
    return waypoint_list


@retry(5)
def mission_add_waypoints(vehicle, waypoint_list, add_dummy=False, timeout=30):
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_ready()
    for waypoint in waypoint_list:
        waypoint_command = Command(
            0, 0, 0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            0, 0, 0,
            ACC_RADIUS,
            0, 0,
            waypoint[0],
            waypoint[1],
            waypoint[2]
        )
        cmds.add(waypoint_command)
    if add_dummy:
        cmds.add(Command(
            0, 0, 0,
            mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
            mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
            0, 0, 0,
            ACC_RADIUS,
            0, 0,
            waypoint_list[-1][0],
            waypoint_list[-1][1],
            waypoint_list[-1][2]
        ))
    cmds.upload(timeout=timeout)


@retry(5)
def mission_add_waypoint(vehicle, waypoint, cmds=None, upload=False, timeout=30):
    if cmds is None:
        cmds = vehicle.commands
        cmds.download()
        cmds.wait_ready()
    waypoint_command = Command(
        0, 0, 0,
        mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
        0, 0, 0,
        ACC_RADIUS,
        0, 0,
        waypoint[0],
        waypoint[1],
        waypoint[2]
    )
    cmds.add(waypoint_command)
    if upload:
        cmds.upload(timeout=timeout)
