from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect
from src.errors import retry
import time


def get_fence_action(vehicle):
    return vehicle.parameters["FENCE_ACTION"]


def set_fence_action(vehicle, val):
    while vehicle.parameters["FENCE_ACTION"] != val:
        vehicle.parameters["FENCE_ACTION"] = val
        time.sleep(0.1)


def set_fence_total(vehicle, val: int):
    while vehicle.parameters["FENCE_TOTAL"] != val:
        vehicle.parameters["FENCE_TOTAL"] = val
        time.sleep(0.1)


def create_mission_geofence(vehicle, seq, total, point):
    return vehicle.message_factory.mission_item_int_encode(
        target_system=0, target_component=0,
        seq=seq,
        frame=dialect.MAV_FRAME_GLOBAL_RELATIVE_ALT,
        command=dialect.MAV_CMD_NAV_FENCE_POLYGON_VERTEX_INCLUSION,
        current=0, autocontinue=0,
        param1=total, param2=0, param3=0, param4=0,
        x=int(point[0] * 1e7),
        y=int(point[1] * 1e7),
        z=0,
        mission_type=dialect.MAV_MISSION_TYPE_FENCE
    )


@retry(5)
def set_geofence(vehicle, points):
    curr_fence_action = get_fence_action(vehicle)
    set_fence_action(vehicle, dialect.FENCE_ACTION_NONE)
    set_fence_total(vehicle, len(points))
    count = len(points)
    init_message = vehicle.message_factory.mission_count_encode(
        target_system=0, target_component=0,
        count=count,
        mission_type=dialect.MAV_MISSION_TYPE_FENCE
    )
    vehicle.send_mavlink(init_message)
    print("Sent MISSION_COUNT")

    ready = False

    # TODO: add timeouts
    def ack_listener(vehicle, name, msg):
        print("Received MISSION_ACK")
        if msg.mission_type != dialect.MAV_MISSION_TYPE_FENCE:
            return
        nonlocal ready
        ready = msg.type == dialect.MAV_MISSION_ACCEPTED

    def mission_request_listener(vehicle, name, msg):
        print("Received MISSION_REQUEST_INT")
        if msg.mission_type != dialect.MAV_MISSION_TYPE_FENCE:
            return
        geofence_point = create_mission_geofence(
            vehicle, msg.seq, len(points), points[msg.seq])
        vehicle.send_mavlink(geofence_point)
        print("Sent MISSION_ITEM_INT")

    vehicle.add_message_listener("MISSION_ACK", ack_listener)
    vehicle.add_message_listener("MISSION_REQUEST", mission_request_listener)

    while not ready:
        pass
    
    set_fence_action(vehicle, curr_fence_action)

    print("Done Uploading")
    vehicle.remove_message_listener("MISSION_ACK", ack_listener)
    vehicle.remove_message_listener("MISSION_REQUEST",
                                    mission_request_listener)


@retry(5)
def enable_fence(vehicle):
    message = vehicle.message_factory.command_long_encode(
        target_system=0, target_component=0,
        command=mavutil.mavlink.MAV_CMD_DO_FENCE_ENABLE,
        confirmation=0,
        param1=1,
        param2=0,
        param3=0,
        param4=0,
        param5=0,
        param6=0,
        param7=0
    )
    vehicle.send_mavlink(message)
    # TODO: add timeouts


def generate_fence(filename):
    fence_list = []
    with open(filename) as f:
        for line in f:
            waypoint = line.strip().split(",")
            fence_list.append([float(coord) for coord in waypoint])
    return fence_list


if __name__ == "__main__":
    from dronekit import connect

    # create mission item list
    target_locations = [(38.31729702009844, -76.55617670782419),
                        (38.31594832826572, -76.55657341657302),
                        (38.31546739500083, -76.55376201277696),
                        (38.31470980862425, -76.54936361414539),
                        (38.31424154692598, -76.54662761646904),
                        (38.31369801280048, -76.54342380058223),
                        (38.31331079191371, -76.54109648475954),
                        (38.31529941346197, -76.54052104837133),
                        (38.31587643291039, -76.54361305817427),
                        (38.31861642463319, -76.54538594175376),
                        (38.31862683616554, -76.55206138505936),
                        (38.31703471119464, -76.55244787859773),
                        (38.31674255749409, -76.55294546866578),
                        (38.31729702009844, -76.55617670782419)]

    vehicle = connect("/dev/ttyACM1", baud=115200, wait_ready=True)
    print("Connected to vehicle")

    set_geofence(vehicle, target_locations)
