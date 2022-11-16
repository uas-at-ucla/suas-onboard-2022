import numpy as np
import cv2
EARTH_RADIUS = 250830000 # 2.5083 x 10^8 inches

# arctan2 (over arctan) is necessary to get rid of angle ambiguity
def tag(alititude: float, latitude: float, longitude: float, heading, sensor_width: float, focal_length: float, 
        image_width: int, image_height: int, target_x: int, target_y: int, verbose = False) -> tuple[float, float]:
    """ 
    Calculates the latitude and longitude of the target given the current location and heading of the drone.
    
    Parameters
    ----------
    altitude : float
        The altitude of the drone in inches.
    latitude : float
        The latitude of the drone in radians.
    longitude : float
        The longitude of the drone in radians.
    heading : float
        The heading of the drone in radians.
    sensor_width : float
        The width of the camera sensor in inches.
    focal_length : float
        The focal length of the camera in inches.
    image_width : int
        The width of the image in pixels.
    image_height : int
        The height of the image in pixels.
    target_x : int
        The x coordinate of the target's center in pixels.
    target_y : int
        The y coordinate of the target's center in pixels.
    verbose : bool
        Display visual of image target and longitude/latitude 
    
    Returns 
    -------
    float, float
        returns the latitude and longitude of the target in radians.
    """
    
    GSD = (sensor_width*alititude) / (focal_length*image_width) # Ground Sample Distance [inches/pixel]
    x_length = (target_x-image_width/2) * GSD # inches from center of image to center of object in the X-direction
    y_length = (target_y-image_height/2) * GSD # inches from center of image to center of object in the Y-direction
    bearing = heading + np.arctan2(x_length,y_length) # radians
    distance = np.sqrt(x_length**2 + y_length**2) # inches from center of image to center of object
    target_lat = np.arcsin(np.sin(latitude)*np.cos(distance/EARTH_RADIUS) + np.cos(latitude)*np.sin(distance/EARTH_RADIUS)*np.cos(bearing))
    target_long = longitude + np.arctan2(np.sin(bearing)*np.sin(distance/EARTH_RADIUS)*np.cos(latitude), np.cos(distance/EARTH_RADIUS)-np.sin(latitude)*np.sin(target_lat))
    if verbose:
        img = np.zeros((image_width, image_height,3), np.uint8)
        center = (int(image_width/2), int(image_height/2))
        cv2.arrowedLine(img,center,(image_width,image_height//2),(255,255,255),1)
        cv2.line(img,center,(image_width//2,image_height),(255,255,255),1)
        cv2.line(img,center,(-image_width,image_height//2),(255,255,255),1)
        cv2.line(img,center,(image_width//2,-image_height),(255,255,255),1)
        
        cv2.line(img,center,(target_x,target_y),(255,0,0),3)
        cv2.circle(img,(target_x,target_y), 5, (0,255,0), -1)
        
        d = min(image_width, image_height)/2
        d*=0.9
        heading_vector = center[0]+int(d*np.cos(heading)),center[1]-int(d*np.sin(heading))
        cv2.arrowedLine(img,center,heading_vector,(0,0,255),3)
        cv2.putText(img, f"({np.rad2deg(latitude):.2E}, {np.rad2deg(longitude):.2E})", center, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, f"({np.rad2deg(target_lat):.2E}, {np.rad2deg(target_long):.2E})", (target_x,target_y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        cv2.putText(img, "N", heading_vector, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        name = f'[inches/pixel]: {GSD:.2f}, LatPerPix: {(GSD/(np.pi*EARTH_RADIUS))*90:.2E}'
        cv2.imshow(name,img)
        cv2.setWindowProperty(name, cv2.WND_PROP_TOPMOST, 1)
        cv2.waitKey(0)
        cv2.destroyAllWindows()
        
    return target_lat, target_long

