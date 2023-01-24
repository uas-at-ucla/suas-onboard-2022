import time

#import dronekit_sitl
#sitl = dronekit_sitl.start_default()
#connection_string = sitl.connection_string()

from dronekit import connect, Command, VehicleMode
from pymavlink import mavutil

METERS_PER_FEET = 0.3048

ACC_RADIUS = 7.62 # 25 feet

CLIMB_ANGLE = 20
DESCENT_ANGLE = 20

AIRFIELD_ALT = 43.2816 # Airfield is 142 feet MSL
MIN_RELATIVE_ALT = 22.86 # 75 feet
MAX_RELATIVE_ALT = 121.92 # 400 feet

# TODO: Use correct connection string for real plane.
connection_string = "127.0.0.1:14550"
vehicle = connect(connection_string, wait_ready=True)

# This function is for testing. TODO: REPLACE
def arm_vehicle():
    print("Vehicle is armable:", vehicle.is_armable)
    while not vehicle.armed:
        vehicle.armed = True
        print("Waiting for vehicle to arm . . .")
        time.sleep(1)

def start_mission():
    while vehicle.mode.name != "AUTO":
        vehicle.mode = VehicleMode("AUTO")
        print("Waiting for mode change to AUTO . . .")
        time.sleep(1)

def mission_add_takeoff():
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
    cmds.upload()

def mission_add_land(landing_point):
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
    cmds.upload()

# TODO: Generate waypoints from waypoints given during competition.
# Note: Altitudes are given in feet MSL(global)
def generate_waypoint_list():
    # Example waypoints: [lat, lon, alt]
    waypoint0 = [-35.3461613, 149.1574008, 125]
    waypoint1 = [-35.3369216, 149.1778803, 150]
    waypoint2 = [-35.3261260, 149.1658642, 175]
    waypoint3 = [-35.3280343, 149.1424613, 200]
    waypoint_list = [waypoint0, waypoint1, waypoint2, waypoint3]
    for waypoint in waypoint_list:
        # Convert altitude to meters
        waypoint[2] *= METERS_PER_FEET
        waypoint[2] -= AIRFIELD_ALT
    return waypoint_list

def mission_add_waypoints(waypoint_list):
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
    cmds.upload()

arm_vehicle()

cmds = vehicle.commands
cmds.clear()
cmds.upload()

mission_add_takeoff()
mission_add_waypoints(generate_waypoint_list())
mission_add_land([-35.3283464, 149.1399348])
start_mission()
