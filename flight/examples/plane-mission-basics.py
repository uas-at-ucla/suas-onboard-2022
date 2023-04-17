import time

from dronekit import connect, Command, VehicleMode
from pymavlink import mavutil

import math
import tkinter as tk

METERS_PER_FEET = 0.3048

ACC_RADIUS = 7.62  # 25 feet

CLIMB_ANGLE = 20
DESCENT_ANGLE = 20

AIRFIELD_ALT = 43.2816  # Airfield is 142 feet MSL
MIN_RELATIVE_ALT = 22.86  # 75 feet
MAX_RELATIVE_ALT = 121.92  # 400 feet

STARTING_POINT = [38.31633, -76.55578]
TERMINATION_POINT = [38.315339, -76.548108]

# TODO: Use correct connection string for real plane.
connection_string = "127.0.0.1:14551"
vehicle = connect(connection_string, wait_ready=True)


# This function is for testing. TODO: REPLACE
def arm_vehicle():
    print("Vehicle is armable:", vehicle.is_armable)
    while not vehicle.is_armable:
        time.sleep(1)
        print("Waiting for vehicle to become armable . . .")
    while not vehicle.armed:
        vehicle.armed = True
        print("Waiting for vehicle to arm . . .")
        time.sleep(1)
    print("ARMED")


# Puts the vehicle into mode.
def mode_switch(flight_mode):
    while vehicle.mode.name != flight_mode:
        vehicle.mode = VehicleMode(flight_mode)
        print("Waiting for mode change to " + flight_mode + " . . .")
        time.sleep(1)
    print(flight_mode)


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


def quaternion(roll=0, pitch=0, yaw=0):
    """
    Convert degrees to quaternions
    """
    t0 = math.cos(math.radians(yaw * 0.5))
    t1 = math.sin(math.radians(yaw * 0.5))
    t2 = math.cos(math.radians(roll * 0.5))
    t3 = math.sin(math.radians(roll * 0.5))
    t4 = math.cos(math.radians(pitch * 0.5))
    t5 = math.sin(math.radians(pitch * 0.5))

    w = t0 * t2 * t4 + t1 * t3 * t5
    x = t0 * t3 * t4 - t1 * t2 * t5
    y = t0 * t2 * t5 + t1 * t3 * t4
    z = t1 * t2 * t4 - t0 * t3 * t5

    return [w, x, y, z]


def set_attitude_target(roll=0, pitch=0, yaw=0, thrust=0.5):
    attitude_quaternion = quaternion(roll, pitch, yaw)
    msg = vehicle.message_factory.set_attitude_target_encode(
        0, 0, 0,
        0b00000111,
        attitude_quaternion,
        0, 0, 0,
        thrust
    )
    vehicle.send_mavlink(msg)


# TODO: Allow combos, holding
def press(event):
    k = event.keysym
    if k == "BackSpace":
        mode_switch("AUTO")
    elif k == "Escape":
        mode_switch("RTL")
    elif k == "g":
        mode_switch("GUIDED")
    elif k == "w":  # Pitch down
        set_attitude_target(pitch=-20)
    elif k == "s":  # Pitch up
        set_attitude_target(pitch=20)
    elif k == "a":  # Roll left
        set_attitude_target(roll=-20)
    elif k == "d":  # Roll right
        set_attitude_target(roll=20)
    elif k == "q":  # Yaw left
        set_attitude_target(yaw=-20)
    elif k == "e":  # Yaw right
        set_attitude_target(yaw=20)
    elif k == "r":  # Throttle up
        set_attitude_target(thrust=1)
    elif k == "f":  # Throttle down
        set_attitude_target(thrust=0)
    elif k == "i":
        print(vehicle.channels["2"])


def release(event):
    k = event.keysym
    if k == "w":
        set_attitude_target(pitch=0)
    elif k == "s":
        set_attitude_target(pitch=0)
    elif k == "a":
        set_attitude_target(roll=0)
    elif k == "d":
        set_attitude_target(roll=0)
    elif k == "q":
        set_attitude_target(yaw=0)
    elif k == "e":
        set_attitude_target(yaw=0)
    elif k == "r":
        set_attitude_target(thrust=0.5)
    elif k == "f":
        set_attitude_target(thrust=0.5)


arm_vehicle()
cmds = vehicle.commands

cmds.clear()
cmds.upload()
mission_add_takeoff()
mission_add_waypoints(generate_waypoint_list("waypoints.txt"))
mission_add_land(TERMINATION_POINT)

tk_root = tk.Tk()
tk_root.bind("<Key>", press)
tk_root.bind("<KeyRelease>", release)
tk_root.mainloop()
