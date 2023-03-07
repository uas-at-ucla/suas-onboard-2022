"""
Detect text and shape color
"""

import cv2
import numpy as np
from scipy import stats

import time
import util


# (color, hue lower bound, hue upper bound)
COLOR_RANGES = [
    ('red', 0, 6), ('orange', 7, 22), ('yellow', 23, 32), ('green', 33, 82),
    ('blue', 83, 126), ('purple', 127, 155), ('red', 156, 180)
]


# Perform kmeans clustering on an image
# and return the clustered image
def kmeans(img, mask=None):

    # Array of truthy values
    if mask is None:
        mask = np.ones(img.shape[0:2], dtype=bool)

    V = np.float32(img.reshape(-1, 3))[mask.flatten()]

    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
    _, labels, centers = cv2.kmeans(V, 2, None, criteria, 10,
                                    cv2.KMEANS_PP_CENTERS)
    centers = np.uint8(centers)
    res = centers[labels.flatten()]

    clustered = np.zeros_like(img.reshape(-1, 3))
    clustered[mask.flatten()] = res

    clustered = np.uint8(clustered).reshape(img.shape)

    return clustered


# Return a mask of all pixels in the image matching the specified color
def get_mask_from_color(img, color):
    mask = np.all(img.reshape(-1, 3) == color, axis=1)
    mask = mask.reshape(img.shape[0:2])
    mask = np.uint8(mask)

    return mask


# Return the average distance from the center
# of all nonzero pixels in the image
def avg_dist(mask, center):
    mask_points = np.transpose(mask.nonzero())
    if not len(mask_points):
        return 0

    distance = sum(np.linalg.norm(point - center) for point in mask_points)

    return distance / len(mask_points)


# Match an rgb code to a color name
def color_name(rgb):
    # h ranges from 0 to 180, l and s range from 0 to 255
    hls = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HLS)[0][0]

    # l, a, and b range from 0 to 255
    lab = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2LAB)[0][0]

    # black detection: lightness <= 40
    if hls[1] <= 40:
        return 'black'

    # white detection: lightness >= 215
    if hls[1] >= 215:
        return 'white'

    # brown detection: values obtained through testing
    b_lower_bound = max([1192-8*lab[1], 132, lab[1]-20])
    if (lab[0] <= 127.5) and (lab[1] <= 160.5) and (lab[2] >= b_lower_bound):
        return "brown"

    # gray detection: a* and b* are close to neutral(128)
    if 118 <= lab[1] <= 138 and 118 <= lab[2] <= 138:
        return 'gray'

    # general color detection, looping through color ranges
    for color in COLOR_RANGES:
        if color[1] <= hls[0] <= color[2]:
            return color[0]


# Perform kmeans clustering to extract the object
# Then cluster repeatedly until text and shape are separated
# Extract the median color and rnn a color detection algorithm
# to detect the color
def get_text_and_shape_color(image):

    # Change to RGB
    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # ---------- EXTRACT OBJECT MASK ---------- #

    blurred = cv2.GaussianBlur(image, (7, 7), 0)
    clustered_img = kmeans(blurred)

    # Extract the background color
    border = np.concatenate((clustered_img[0], clustered_img[-1],
                            clustered_img[:, 0], clustered_img[:, -1]))
    bg_color = stats.mode(border, keepdims=True)[0][0]

    # Exclude the background color
    cluster_mask = np.logical_xor(np.ones(image.shape[0:2]),
                                  get_mask_from_color(clustered_img, bg_color))
    cluster_mask = np.uint8(cluster_mask)

    # Fill it in by taking the largest contour

    # First dilate it
    kernel = np.ones((3, 3), np.uint8)
    cluster_mask = cv2.dilate(cluster_mask, kernel)

    kernel = np.ones((5, 5), np.uint8)
    cluster_mask = cv2.morphologyEx(cluster_mask, cv2.MORPH_CLOSE, kernel)

    # Then contour it
    contours, _ = cv2.findContours(cluster_mask, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
    largest = max(contours, key=cv2.contourArea)

    cluster_mask = cv2.drawContours(np.zeros(image.shape[0:2]),
                                    [largest], -1, 255, -1)
    cluster_mask = np.uint8(cluster_mask)

    # erode the cluster mask
    kernel = np.ones((5, 5), np.uint8)
    cluster_mask = cv2.erode(cluster_mask, kernel)

    cluster_mask = cluster_mask.astype(bool)

    # ---------- EXTRACT TEXT MASK AND SHAPE MASK ---------- #

    # Calculate mask center using contour moments
    M = cv2.moments(np.uint8(cluster_mask))
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    center = np.array([cY, cX])

    # Extract the text and shape masks
    shape_mask = np.zeros_like(cluster_mask)
    text_mask = np.zeros_like(cluster_mask)

    # count iterations just in case
    it = 0

    # Repeat this process until the text is closer to the mask center
    while avg_dist(text_mask, center) >= avg_dist(shape_mask, center) \
            and it < 5:

        # Remove the text and repeat the cluster process each time
        # For the first iteration, the text mask is empty
        cluster_mask = np.logical_xor(cluster_mask, text_mask)

        # Cluster
        clustered_img = kmeans(blurred, mask=cluster_mask)
        clustered_pixels = clustered_img.reshape(-1, 3)[cluster_mask.flatten()]

        # Extract the masks
        shape_color = stats.mode(clustered_pixels, keepdims=True)[0][0]

        # If the shape color was (0, 0, 0), which would match the background
        if np.array_equal(shape_color, (0, 0, 0)):
            clustered_img[np.all(clustered_img == shape_color, axis=2) &
                          (cluster_mask)] += 1
            shape_color += 1

        shape_mask = get_mask_from_color(clustered_img, shape_color)
        text_mask = np.logical_xor(cluster_mask, shape_mask)
        text_mask = np.uint8(text_mask)

        # take the largest contour from the text
        cnts, _ = cv2.findContours(text_mask, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)
        largest = cv2.drawContours(np.zeros(image.shape[0:2]),
                                   [max(cnts, key=cv2.contourArea)],
                                   -1, 255, -1)

        # Take the intersection of the largest and the text mask
        text_mask = cv2.bitwise_and(text_mask, text_mask,
                                    mask=np.uint8(largest))
        text_mask = np.uint8(text_mask)

        # Calculate mask center using contour moments for next iteration
        M = cv2.moments(np.uint8(cluster_mask))
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        center = np.array([cY, cX])

        it += 1

    # Logging
    if (it == 5):
        util.error("ERROR. WHILE LOOP RUN TOO MAY TIMES")

    util.debug_imwrite(text_mask,
                       f"./images/debug/text-mask-{time.time()}.jpg")
    util.debug_imwrite(shape_mask,
                       f"./images/debug/shape-mask-{time.time()}.jpg")

    # ---------- MASK CLEANUP + PIXEL EXTRACTION --------- #
    # Try eroding with 5x5 kernel
    if cv2.erode(text_mask, np.ones((5, 5), np.uint8)).any():
        text_mask = cv2.erode(text_mask, np.ones((5, 5), np.uint8))

    # Otherwise erode with 3x3 kernel
    elif cv2.erode(text_mask, np.ones((3, 3), np.uint8)).any():
        text_mask = cv2.erode(text_mask, np.ones((3, 3), np.uint8))

    # Otherwise no erosion

    # Extract the pixels
    shape_pixels = cv2.bitwise_and(image, image, mask=shape_mask)
    shape_pixels = shape_pixels.reshape(-1, 3)

    text_pixels = cv2.bitwise_and(image, image, mask=text_mask)
    text_pixels = text_pixels.reshape(-1, 3)

    # Get median color
    text_pixels = text_pixels[np.any(text_pixels, axis=1)]
    text_rgb = np.median(text_pixels, axis=0)

    shape_pixels = shape_pixels[np.any(shape_pixels, axis=1)]
    shape_rgb = np.median(shape_pixels, axis=0)

    # Get color name
    text_color = color_name(text_rgb)
    shape_color = color_name(shape_rgb)

    return (text_color, shape_color)
