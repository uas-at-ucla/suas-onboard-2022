"""
Detect text and shape color
"""

import cv2
import numpy as np

from odlc.segmentation import get_text_and_shape_mask

# (color, hue lower bound, hue upper bound)
COLOR_RANGES = [
    ('red', 0, 6), ('orange', 7, 22), ('yellow', 23, 32), ('green', 33, 82),
    ('blue', 83, 126), ('purple', 127, 155), ('red', 156, 180)
]


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


# Extract the median color and rnn a color detection algorithm
# to detect the color
def get_text_and_shape_color(image):

    image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    text_mask, shape_mask = get_text_and_shape_mask(image)

    # Cleanup the masks
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
