import os
import logging
import subprocess
import sys
import re
from datetime import datetime
from GPSPhoto import gpsphoto
import geopy
import geopy.distance
import signal
import psutil
# from PIL import Image
# from PIL.ExifTags import TAGS, GPSTAGS
# from exif import Image
# Uncomment following line to redirect all logging to STDOUT
logging.basicConfig(stream=sys.stdout, level=logging.DEBUG)
log = logging.getLogger(__name__)


class PixCam:
    # Constructor: initializes array of command-line args, checks working
    # directory and gphoto2 installation
    # Can accept optional camera argument (currently unused)
    def __init__(self, working_dir, camera="Sony Alpha-A5000 (Control)"):
        self.args = ["gphoto2"]

        # Check working directory
        if not os.path.isdir(working_dir) or not os.path.isabs(working_dir):
            raise FileNotFoundError("Invalid absolute directory path")
        self.working_dir = working_dir
        log.info('Working directory: %s', working_dir)
        # set an arg flag to create a custom, time-based naming system for
        # images
        self.set_flag("--filename", r"'{0}{1}%Y-%m-%d--%H-%M-%S.%C'"
                      .format(working_dir, os.path.sep))

        # Crude check that gphoto2 is installed
        try:
            if "Usage" not in subprocess.check_output('gphoto2') \
                    .decode('ascii'):
                raise Exception()
            log.info("gphoto2 installation identified")
        except Exception:
            log.error("gphoto2 not set up")
            raise SystemError("gphoto2 not set up")

        # Crude check that camera is connected
        if not self.check_camera_connection():
            log.error("Cannot find camera")
            raise SystemError("Cannot find camera")
        log.info("Camera connected")

    # Take a picture and return picture path and picture name or None in case
    # of failure
    def take_pic(self):
        log.info("Taking a picture")
        output = self.execute_cmd("--capture-image-and-download")
        if output == None:
            return None, None
        log.info("Output: %s", output)
        image_path = re.search("Saving file as (.*?)[\n]", output).group(1)
        return image_path, os.path.basename(image_path)

    # Run any command with necessary flags prefixed and return
    # readable/writeable output
    # In case of an error, returns None and logs error
    def execute_cmd(self, cmd):
        try:
            command_str = ' '.join(self.args + [cmd])
            log.info("Executing command: %s", command_str)
            p = subprocess.Popen([command_str], shell=True, stdout=subprocess.PIPE)
            out, _ = p.communicate(timeout=5)
            if p.returncode == 0:
                return out.decode("ascii")
            else:
                return None
        except subprocess.TimeoutExpired as e:
            log.error("Command timed out: %s", e)
            current_process = psutil.Process()
            children = current_process.children(recursive=True)
            for child in children:
                os.kill(child.pid, signal.SIGKILL)
            return None

    # Takes a picture and embeds crude gps data into metadata
    # Use if drone is stationary
    # Lat/Long in DD with sign, alt in ft ASL
    # Ex. 45, -40, 400
    def take_pic_and_record_loc(self, lat, long, alt=0):
        image_path, image_name = self.take_pic()

        if image_path == None:
            return None, None

        # with open(image_path, "rb") as image_file:
        #     image = Image(image_file)
        #
        # print(image_old_date)
        image_datetime = self.get_datetime_from_img_name(image_name)
        # print(image_datetime)
        image_new_date = self.get_exif_date_from_datetime(image_datetime)
        # print(image.get("datetime"))
        # print(image_new_date)

        # Convert GPS data from DD to DMS
        # lat_abs = abs(lat)
        # long_abs = abs(long)
        # if lat < 0:
        #     lat_ref = "S"
        # else:
        #     lat_ref = "N"
        # if long < 0:
        #     long_ref = "W"
        # else:
        #     long_ref = "E"

        self.add_gps_metadata(image_path, lat, long, image_new_date, alt=alt)
        log.info("Recorded gps coordinated to image metadata")

        return image_path, image_name

    def add_gps_metadata(self, image_path, lat, long, timestamp, alt=0):
        # Convert alt to m
        alt = int(alt * 0.3048)

        log.info("Recording gps coordinates: %f, %f", lat, long)
        photo = gpsphoto.GPSPhoto(image_path)
        info = gpsphoto.GPSInfo((lat, long), timeStamp=timestamp, alt=alt)
        photo.modGPSData(info, image_path)

    def get_datetime_from_img_name(self, image_name):
        return datetime.strptime(image_name.split(".")[0],
                                 "%Y-%m-%d--%H-%M-%S")
        # "yyyy-MM-dd--HH-mm-ss"

    def get_exif_date_from_datetime(self, dt):
        return dt.strftime("%Y:%m:%d %H:%M:%S")  # yyyy:MM:dd HH:mm:ss

    # Mathematical conversion from decimal degrees to degrees/minutes/seconds.
    # Returns tuple.
    def dd_to_dms(self, dd):
        degrees = int(dd)
        minutes = int(60*(dd-degrees))
        seconds = int(3600*(dd-degrees-(minutes/float(60))))
        return degrees, minutes, seconds

    # Takes a picture and embeds adjusted gps data into metadata
    # Use if drone is moving. Inherently flawed since the precision of the
    # filename is to the second
    # Velocity in ft/s, heading in degrees
    def take_pic_and_adjust_loc(self, lat, long, velocity, heading, alt=0):
        # Find how much time passes between GPS reading and picture snap
        init_time_sec = float(datetime.now().timestamp())
        image_path, image_name = self.take_pic()

        if image_path == None:
            return None, None

        timestamp_datetime = self.get_datetime_from_img_name(image_name)
        timestamp = self.get_exif_date_from_datetime(timestamp_datetime)
        final_time_sec = float(timestamp_datetime.timestamp())
        seconds_passed = final_time_sec - init_time_sec

        distance = seconds_passed * velocity
        # Find new GPS location
        start_coord = geopy.Point(lat, long)
        end_point = geopy.distance.geodesic(feet=distance) \
            .destination(start_coord, heading)
        new_lat = end_point.latitude
        new_long = end_point.longitude

        self.add_gps_metadata(image_path,
                              new_lat,
                              new_long,
                              timestamp,
                              alt=alt)
        return image_path, image_name

    # Returns true if camera is found, false otherwise
    def check_camera_connection(self):
        try:
            output = self.execute_cmd("--summary")
            if "*** Error: No camera found. ***" in output:
                return False
            return True
        except Exception:
            return False

    # Set flag: key and value represent flag and option respectively:
    # ex. -f filename -> "-f" is the key, "filename" is the value
    # This is converted to a string and added to command-line args for gphoto2
    def set_flag(self, key, value):
        log.info("Attempting to add/update key value pair %s:%s", key, value)
        if not key.startswith("-"):
            raise ValueError("Key must start with -")
        if key in self.args:
            log.info("Existing flag found. Updating...")
            index = self.args.index(key)
            self.args[index+1] = value
        else:
            log.info("Existing flag not found. Adding...")
            self.args.extend([key, value])

    def get_flag(self, key):
        if key in self.args:
            index = self.args.index(key)
            value = self.args[index + 1]
            log.info("Flag %s found, value: %s", key, value)
            return value
        else:
            log.info("Flag %s not found", key)
            return None

    def __del__(self):
        pass

    def take_picture(self):
        res1, _ = self.take_pic_and_adjust_loc(34.068458, -118.442819, 40, 0)
        return res1

if __name__ == "__main__":
    print("Initiating testing protocol")

