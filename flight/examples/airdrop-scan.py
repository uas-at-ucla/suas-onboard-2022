# def airdrop_scan(vehicle, boundary_points, altitude):
#     # Define the search area boundaries
#     lat_min = min(p[0] for p in boundary_points)
#     lat_max = max(p[0] for p in boundary_points)
#     lon_min = min(p[1] for p in boundary_points)
#     lon_max = max(p[1] for p in boundary_points)

#     # Set the altitude of the vehicle
#     vehicle.simple_takeoff(altitude)

#     # Scan the search area for targets
#     for lat in np.arange(lat_min, lat_max, 0.0001):
#         for lon in np.arange(lon_min, lon_max, 0.0001):
#             # Check if the current location is within the search area
# boundaries
#             if is_point_inside_polygon(lat, lon, boundary_points):
#                 # Move the vehicle to the current location
#                 vehicle.simple_goto(LocationGlobalRelative(lat, lon,
# altitude))

#                 # Wait for the vehicle to reach the current location
#                 while True:
#                     remaining_distance = get_distance_metres(
# vehicle.location.global_frame, LocationGlobalRelative(lat, lon, altitude))
#                     if remaining_distance <= 1:
#                         break
#                     time.sleep(1)

#                 # Take a picture
#                 vehicle.message_factory.command_long_send(
#                     0, 0,  # target system, target component
#                     mavutil.mavlink.MAV_CMD_DO_SET_CAM_TRIGG_DIST,  # command
#                     0,  # confirmation
#                     0,  # param1
#                     0,  # param2
#                     0,  # param3
#                     0,  # param4
#                     1,  # param5 (1 = take picture)
#                     0,  # param6
#                     0)  # param7

#     # Land the vehicle
#     vehicle.mode = VehicleMode("LAND")
