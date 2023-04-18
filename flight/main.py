import argparse
from dronekit import connect
from src.arm import arm
from src.mission import mission_add_takeoff, \
    generate_waypoint_list, mission_add_waypoints, \
    mission_add_land, start_mission
from pymavlink import mavutil
import time


# TODO: move
WAYPOINT_FILENAME = "waypoints.txt"
# RTL_POINT = [38.315339, -76.548108]
RTL_POINT = [34.17563223420202, -118.48213260580246] # Apollo RTL

# MANUAL_MODES = ["MANUAL", "FBWA"]

def main(args):
    connection_string = args.connect
    waypoint_file = args.waypoint_file if args.waypoint_file else WAYPOINT_FILENAME

    # Connect to the Vehicle
    print('Connecting to vehicle on: %s' % connection_string)
    vehicle = connect(connection_string, wait_ready=True, timeout=360, baud=115200)

    # arm(vehicle)

    while not (vehicle.armed and vehicle.mode.name != "LOITER" and vehicle.altitude < 22.86):
        time.sleep(1)
        pass

    print("Starting Autopilot")

    # Setup waypoint mission
    mission_add_takeoff(vehicle)
    waypoints = generate_waypoint_list(waypoint_file)
    mission_add_waypoints(vehicle, waypoints)
    mission_add_land(vehicle, RTL_POINT)
    print("Uploaded mission")

    # Start mission
    # print("Starting waypoint mission")
    # start_mission(vehicle)

    # mission_not_done = True

    # while mission_not_done:
    #     pass

    # Start airdrop scan
    # TODO: do

    # Airdrop
    # TODO: do

    # Land
    # TODO: copy from above


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Commands vehicle using vehicle.simple_goto.')
    parser.add_argument('--connect',
                        help="Vehicle connection target string. \
                        If not specified, SITL automatically \
                            started and used.")
    parser.add_argument('--waypoint_file',
                        help="File name of the waypoints to be flown through.")
    args = parser.parse_args()

    main(args)
