"""
    Send MISSION_COUNT message to the vehicle first
    Vehicle will respond to this with MISSION_REQUEST message
    This message contains requested mission item sequence number
    Respond to this message with MISSION_ITEM_INT message as soon as possible
    Vehicle will wait and re-request the MISSION_ITEM_INT messages with limited time and timeout
    After sending the last mission item, vehicle will send MISSION_ACK message

    https://mavlink.io/en/messages/common.html#MISSION_COUNT
    https://mavlink.io/en/messages/common.html#MISSION_REQUEST
    https://mavlink.io/en/messages/common.html#MISSION_ITEM_INT
    https://mavlink.io/en/messages/common.html#MISSION_ACK
"""

import time
from pymavlink import mavutil
import pymavlink.dialects.v20.all as dialect
FENCE_TOTAL = "FENCE_TOTAL".encode(encoding="utf-8")
FENCE_ACTION = "FENCE_ACTION".encode(encoding="utf8")
FENCE_ALT_MAX = "FENCE_ALT_MAX".encode(encoding="utf8")
FENCE_RADIUS = "FENCE_RADIUS".encode(encoding="utf8")
PARAM_INDEX = -1

# create mission item list
target_locations = [(38.31729702009844,-76.55617670782419),
                    (38.31594832826572,-76.55657341657302),
                    (38.31546739500083,-76.55376201277696),
                    (38.31470980862425,-76.54936361414539),
                    (38.31424154692598,-76.54662761646904),
                    (38.31369801280048,-76.54342380058223),
                    (38.31331079191371,-76.54109648475954),
                    (38.31529941346197,-76.54052104837133),
                    (38.31587643291039,-76.54361305817427),
                    (38.31861642463319,-76.54538594175376),
                    (38.31862683616554,-76.55206138505936),
                    (38.31703471119464,-76.55244787859773),
                    (38.31674255749409,-76.55294546866578),
                    (38.31729702009844,-76.55617670782419)]


# connect to vehicle
vehicle = mavutil.mavlink_connection(device="udpin:127.0.0.1:14551")

# wait for a heartbeat
vehicle.wait_heartbeat()

# inform user
print("Connected to system:", vehicle.target_system, ", component:", vehicle.target_component)


# create PARAM_REQUEST_READ message
message = dialect.MAVLink_param_request_read_message(target_system=vehicle.target_system,
                                                     target_component=vehicle.target_component,
                                                     param_id=FENCE_ACTION,
                                                     param_index=PARAM_INDEX)

# send PARAM_REQUEST_READ message to the vehicle
vehicle.mav.send(message)

# ---------------------------------------------------------GETS FENCE ACTION--------------------------------------------------------------------------
while True:

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_ACTION
    if message["param_id"] == "FENCE_ACTION":
        # get the original fence action parameter from vehicle
        fence_action_original = int(message["param_value"])

        # break the loop
        break

# debug parameter value
print("FENCE_ACTION parameter original:", fence_action_original)

# ---------------------------------------------------------SETS FENCE ACTION TO 0--------------------------------------------------------------------------
while True:

    # create parameter set message
    message = dialect.MAVLink_param_set_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                param_id=FENCE_ACTION,
                                                param_value=dialect.FENCE_ACTION_NONE,
                                                param_type=dialect.MAV_PARAM_TYPE_REAL32)

    # send parameter set message to the vehicle
    vehicle.mav.send(message)

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_ACTION
    if message["param_id"] == "FENCE_ACTION":

        # make sure that parameter value reset successfully
        if int(message["param_value"]) == dialect.FENCE_ACTION_NONE:
            print("FENCE_ACTION reset to 0 successfully")

            # break the loop
            break

        # should send param set message again
        else:
            print("Failed to reset FENCE_ACTION to 0, trying again")

# ---------------------------------------------------SET FENCE TOTAL TO 0 TO DISABLE THE INITIAL FENCE----------------------------------------------------
while True:

    # create parameter reset message
    message = dialect.MAVLink_param_set_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                param_id=FENCE_TOTAL,
                                                param_value=0,
                                                param_type=dialect.MAV_PARAM_TYPE_REAL32)

    # send parameter reset message to the vehicle
    vehicle.mav.send(message)

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_TOTAL
    if message["param_id"] == "FENCE_TOTAL":

        # make sure that parameter value set successfully
        if int(message["param_value"]) == 0:
            print("FENCE_TOTAL reset to 0 successfully")

            # break the loop
            break

        # should send param reset message again
        else:
            print("Failed to reset FENCE_TOTAL to 0")

# ---------------------------------------------------SET FENCE TOTAL TO NUM OF FENCES---------------------------------------------------------------------
while True:

    # create parameter set message
    message = dialect.MAVLink_param_set_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                param_id=FENCE_TOTAL,
                                                param_value=len(target_locations),
                                                param_type=dialect.MAV_PARAM_TYPE_REAL32)

    # send parameter set message to the vehicle
    vehicle.mav.send(message)

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_TOTAL
    if message["param_id"] == "FENCE_TOTAL":

        # make sure that parameter value set successfully
        if int(message["param_value"]) == len(target_locations):
            print("FENCE_TOTAL set to {0} successfully".format(len(target_locations)))

            # break the loop
            break

        # should send param set message again
        else:
            print("Failed to set FENCE_TOTAL to {0}".format(len(target_locations)))

# ---------------------------------------------------------SETS FENCE ACTION BACK TO ORIGINAL--------------------------------------------------------------------------
while True:

    # create parameter set message
    message = dialect.MAVLink_param_set_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                param_id=FENCE_ACTION,
                                                param_value=fence_action_original,
                                                param_type=dialect.MAV_PARAM_TYPE_REAL32)

    # send parameter set message to the vehicle
    vehicle.mav.send(message)

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_ACTION
    if message["param_id"] == "FENCE_ACTION":

        # make sure that parameter value set successfully
        if int(message["param_value"]) == fence_action_original:
            print("FENCE_ACTION set to original value {0} successfully".format(fence_action_original))

            # break the loop
            break

        # should send param set message again
        else:
            print("Failed to set FENCE_ACTION to original value {0} ".format(fence_action_original))

# ---------------------------------------------------------SET FENCES----------------------------------------------------------------------------------
message = dialect.MAVLink_mission_count_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                count=len(target_locations),
                                                mission_type=dialect.MAV_MISSION_TYPE_FENCE)

# send mission count message to the vehicle
vehicle.mav.send(message)

# this loop will run until receive a valid MISSION_ACK message
while True:

    # catch a message
    message = vehicle.recv_match(blocking=True)

    # convert this message to dictionary
    message = message.to_dict()

    # check this message is MISSION_REQUEST
    if message["mavpackettype"] == dialect.MAVLink_mission_request_message.msgname:

        # check this request is for mission items
        if message["mission_type"] == dialect.MAV_MISSION_TYPE_FENCE:

            # get the sequence number of requested mission item
            seq = message["seq"]

            print(seq)
            message = dialect.MAVLink_mission_item_int_message(target_system=vehicle.target_system,
                                                                target_component=vehicle.target_component,
                                                                seq=seq,
                                                                frame=dialect.MAV_FRAME_GLOBAL_RELATIVE_ALT,
                                                                command=dialect.MAV_CMD_NAV_FENCE_POLYGON_VERTEX_INCLUSION,
                                                                current=0,
                                                                autocontinue=0,
                                                                param1=len(target_locations),
                                                                param2=0,
                                                                param3=0,
                                                                param4=0,
                                                                x=int(target_locations[seq][0] * 1e7),
                                                                y=int(target_locations[seq][1] * 1e7),
                                                                z=50,
                                                                mission_type=dialect.MAV_MISSION_TYPE_FENCE)

            # send the mission item int message to the vehicle
            vehicle.mav.send(message)

    # check this message is MISSION_ACK
    elif message["mavpackettype"] == dialect.MAVLink_mission_ack_message.msgname:

        # check this acknowledgement is for mission and it is accepted
        if message["mission_type"] == dialect.MAV_MISSION_TYPE_FENCE and \
                message["type"] == dialect.MAV_MISSION_ACCEPTED:
            # break the loop since the upload is successful
            print("Mission upload is successful")
            break

# -----------------------------------------------------------------------ENABLE FENCE------------------------------------------------------------------------------------------------
message = mavutil.mavlink.MAVLink_command_long_message(target_system=vehicle.target_system,
                                               target_component=vehicle.target_component,
                                               command=mavutil.mavlink.MAV_CMD_DO_FENCE_ENABLE,
                                               confirmation=0,
                                               param1=1,
                                               param2=0,
                                               param3=0,
                                               param4=0,
                                               param5=0,
                                               param6=0,
                                               param7=0)

# send the message to the vehicle
vehicle.mav.send(message)


while True:

    # create parameter set message
    message = dialect.MAVLink_param_set_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                param_id=FENCE_ALT_MAX,
                                                param_value=999,
                                                param_type=dialect.MAV_PARAM_TYPE_REAL32)

    # send parameter set message to the vehicle
    vehicle.mav.send(message)

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_TOTAL
    if message["param_id"] == "FENCE_ALT_MAX":

        # make sure that parameter value set successfully
        if int(message["param_value"]) == 999:
            print("FENCE_ALT_MAX set to {0}m successfully".format(999))

            # break the loop
            break

        # should send param set message again
        else:
            print("Failed to set FENCE_ALT_MAX to {0}m".format(999))

while True:

    # create parameter set message
    message = dialect.MAVLink_param_set_message(target_system=vehicle.target_system,
                                                target_component=vehicle.target_component,
                                                param_id=FENCE_RADIUS,
                                                param_value=10000,
                                                param_type=dialect.MAV_PARAM_TYPE_REAL32)

    # send parameter set message to the vehicle
    vehicle.mav.send(message)

    # wait for PARAM_VALUE message
    message = vehicle.recv_match(type=dialect.MAVLink_param_value_message.msgname,
                                 blocking=True)

    # convert the message to dictionary
    message = message.to_dict()

    # make sure this parameter value message is for FENCE_TOTAL
    if message["param_id"] == "FENCE_RADIUS":

        # make sure that parameter value set successfully
        if int(message["param_value"]) == 10000:
            print("FENCE_ALT_MAX set to {0}m successfully".format(10000))

            # break the loop
            break

        # should send param set message again
        else:
            print("Failed to set FENCE_ALT_MAX to {0}m".format(10000))

