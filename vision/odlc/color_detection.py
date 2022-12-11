"""
Detect text and shape color
"""

import cv2
import numpy as np


# (color, hue lower bound, hue upper bound)
COLOR_RANGES = [
    ('red', 0, 7), ('orange', 8, 19), ('yellow', 20, 32), ('green', 33, 82),
    ('blue', 83, 122), ('purple', 123, 155), ('red', 156, 180)
]


# Input image should be cropped so that
# the image only contains one target.
# Draw contours on the image. Filter out
# shadows and small contours of noise, leaving
# behind just the shape, text, and any holes
# in the text. Then just calculate the median
# color of the text and the shape.


# @param img_path: cropped image filepath
# @return tuple of color names: (text color, shape color)


def get_text_and_shape_color(img):

    # Convert image to RGB since OpenCV reads images in BGR
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

    # Slight blur to remove noise in text pixels
    img = cv2.medianBlur(img, 3)

    # ------ DRAWING CONTOURS ------ #

    # Now we will draw contours around each object in the image
    # e.g. contours for the shape and text

    # Use the canny operator to create a mask of the edges
    canny = cv2.Canny(img, 100, 200)

    # Dilate (expand) it so that edges are connected
    kernel = np.ones((2, 2), np.uint8)
    canny = cv2.dilate(canny, kernel)

    # Find the contours
    contours, hierarchy = cv2.findContours(canny, cv2.RETR_CCOMP,
                                           cv2.CHAIN_APPROX_SIMPLE)

    # Some basic reformatting to make things easier
    contours = np.array(contours, dtype=object)
    hierarchy = hierarchy[0]

    # ------ REMOVING CONTOURS OF SHADOWS AND SMALL NOISE ------ #

    final_contours = []

    # Loop through the different hierarchy levels,
    # skipping the -1 level since it contains the outer edge contours
    # and we only want the inner edge contours.

    # This removes the shadows since the outer edge
    # draws a contour around both the shadow and shape,
    # but the inner edge will draw one contour for the shape
    # and a separate one for the shadow.
    # We then eliminate the shadow by looking at
    # all the contours along the inner edge
    # and taking the contour with the largest area
    # (which also removes the small contours of noise).

    # get the different levels so we can loop through them
    levels = np.unique(hierarchy[:, 3])

    # skip the first level (-1)
    for level in levels[1::]:

        # get the contours of the current level
        cnts = contours[hierarchy[:, 3] == level]

        # Add the contour with the largest area to the contour list
        final_contours.append(max(cnts, key=cv2.contourArea))

    # Sort contours with the outer layers first and the inner layers last
    final_contours = final_contours[::-1]

    # ------ MASKING ------ #

    empty_img = np.zeros(img.shape[0:2])

    # Draw the masks. The first (outermost) contour is the shape.
    # The next outermost contour is the text.
    shape_mask = cv2.drawContours(empty_img.copy(), final_contours, 0, 255, -1)
    text_mask = cv2.drawContours(empty_img.copy(), final_contours, 1, 255, -1)

    # Any additional contours are holes
    # Loop through additional contours and remove them from the text
    for i in range(2, len(final_contours)):

        hole_mask = cv2.drawContours(empty_img.copy(),
                                     final_contours, i, 255, -1)

        # Remove the hole mask from the text mask
        text_mask = np.logical_xor(text_mask, hole_mask)

    # Remove the text mask from the shape mask
    shape_mask = np.logical_xor(shape_mask, text_mask)

    # reformat
    shape_mask = np.uint8(shape_mask)
    text_mask = np.uint8(text_mask)

    # Erode (contract) both masks to reverse the dilation performed earlier
    shape_mask = cv2.erode(shape_mask, kernel)
    text_mask = cv2.erode(text_mask, kernel)

    # Use the mask on the color image to extract the pixels
    shape_pixels = cv2.bitwise_and(img, img, mask=shape_mask)
    text_pixels = cv2.bitwise_and(img, img, mask=text_mask)

    # ------ COLOR EXTRACTION ------ #

    # reshape into just an array of pixels
    shape_pixels = shape_pixels.reshape(-1, 3)
    text_pixels = text_pixels.reshape(-1, 3)

    # Extract the pixels that aren't empty
    shape_pixels = shape_pixels[np.any(shape_pixels, axis=1)]
    text_pixels = text_pixels[np.any(text_pixels, axis=1)]

    # Compute the median color
    # since median is more robust than mean
    shape_rgb = np.median(shape_pixels, axis=0)
    text_rgb = np.median(text_pixels, axis=0)

    # Get the color name
    shape_color = color_name(shape_rgb)
    text_color = color_name(text_rgb)

    return (text_color, shape_color)


def color_name(rgb):
    # color conversions
    hsv = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HSV)[0][0]
    hls = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2HLS)[0][0]
    lab = cv2.cvtColor(np.uint8([[rgb]]), cv2.COLOR_RGB2LAB)[0][0]

    # TODO: BROWN DETECTION

    # black detection: lightness <= 50
    if hls[1] <= 50:
        return 'black'

    # white detection: lightness >= 235
    if hls[1] >= 225:
        return 'white'

    # gray detection: a* and b* are close to neutral(128)
    if 118 <= lab[1] <= 138 and 118 <= lab[2] <= 138:
        return 'gray'

    # general color detection, looping through color ranges
    for color in COLOR_RANGES:
        if color[1] <= hsv[0] <= color[2]:
            return color[0]
