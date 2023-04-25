import argparse
from dronekit import connect
from src.mission import \
    generate_waypoint_list, mission_add_waypoints, \
    start_mission, mission_reset, \
    mode_switch
from src.fences import set_geofence, enable_fence, generate_fence
import random
import time


# TODO: move
WAYPOINT_FILENAME = "waypoints.txt"
FENCE_FILENAME = "fence.txt"
# RTL_POINT = [38.315339, -76.548108]
RTL_POINT = [34.17563223420202, -118.48213260580246]  # Apollo RTL

# MANUAL_MODES = ["MANUAL", "FBWA"]


def send_status(vehicle, status: str):
    N = len(status)
    if N <= 50:
        message = vehicle.message_factory.statustext_encode(
            severity=0,
            text=bytes(status, "utf-8")
        )
        vehicle.send_mavlink(message)
    else:
        return
        id = (2**16-1) * random.random()
        for i in range(int(N / 50)):
            message = vehicle.message_factory.statustext_encode(
                severity=6,
                text=status[i*50: i*50+50],
                id=id,
                chunk_seq=i
            )
            vehicle.send_mavlink(message)
        message = vehicle.message_factory.statustext_encode(
            severity=6,
            text=status[i*50:],
            id=id,
        )
        vehicle.send_mavlink(message)
    print(status)


def main(args):
    connection_string = args.connect
    waypoint_file = args.waypoint_file if args.waypoint_file \
        else WAYPOINT_FILENAME
    fence_file = args.fence_file if args.fence_file else FENCE_FILENAME

    # Connect to the Vehicle
    print('Connecting to vehicle on: %s' % connection_string)
    vehicle = connect(connection_string, wait_ready=True,
                      timeout=360, baud=115200)

    send_status(vehicle, "Resetting mission")
    mission_reset(vehicle)

    # Upload fences
    # fence_points = generate_fence(fence_file)
    # set_geofence(vehicle, fence_points)
    # enable_fence(vehicle)

    # Setup waypoint mission
    # waypoints = generate_waypoint_list(waypoint_file)
    # N = len(waypoint_file)
    # mission_add_waypoints(vehicle, waypoints, add_dummy=True)
    # send_status(vehicle, "Uploaded mission")

    # Transition to autonomous mode
    print("Waiting for loiter mode")
    while not (vehicle.armed and vehicle.mode.name != "LOITER" and
               vehicle.altitude >= 22.86):
        time.sleep(0.5)
        pass

    send_status(vehicle, "Starting Autopilot")

    # Start mission
    send_status(vehicle, "Starting waypoint mission")
    start_mission(vehicle)

    while vehicle.commands.next != N + 1:
        time.sleep(0.5)
        pass

    # Start airdrop scan
    # TODO: do

    # Airdrop
    # TODO: do

    # Switch to manual
    mode_switch(vehicle, "LOITER")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description='Commands vehicle using vehicle.simple_goto.')
    parser.add_argument('--connect',
                        help="Vehicle connection target string. \
                        If not specified, SITL automatically \
                            started and used.")
    parser.add_argument('--waypoint_file',
                        help="File name of the waypoints to be flown through.")
    parser.add_argument('--fence_file',
                        help="File name of the waypoints to be flown through.")
    args = parser.parse_args()

    main(args)
