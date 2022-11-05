"""
Detect text and shape color
"""

import numpy as np
import cv2


# Input image should be cropped so that
# the image only contains one target.
# Performs k-means clustering on the image to segment it
# into 3 colors: background, shape, and color.
# Then determines which color corresponds to which object
# and performs color matching using predefined HSV color ranges.


# @param img_path: cropped image filepath
# @return tuple of color names: (text color, shape color)


def get_text_and_shape_color(img_path):

    # Read in the image
    img = cv2.imread(img_path)

    # Convert image to L*a*b color space for better clustering results
    img = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)

    # Format the image data so it's just a list of pixels
    # We do this so it fits the OpenCV clustering function
    vectorized = img.reshape((-1, 3))
    vectorized = np.float32(vectorized)

    # Convert from OpenCV L*a*b to standard L*a*b
    # since it provides more accurate clustering.
    # OpenCV's L channel ranges from 0-255
    # while the standard L channel ranges from 0-100.

    L_SCALE_FACTOR = 100/255

    # Do the conversion on the L channel (the first channel)
    for pixel in vectorized:
        pixel[0] *= L_SCALE_FACTOR

    # K-MEANS CLUSTERING
    # stop when either epsilon (accuracy 1.0) is reached
    # or when max iterations (10) is reached
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)

    # 3 clusters: background, shape, text
    K = 3

    # Run the algorithm 10 times
    attempts = 10

    # OpenCV provides a kmeans function:
    # compactness: sum of squared distance from each point to their centers
    # labels: array where each pixel is marked with a cluster label
    # colors: the centers of clusters (L*a*b values in this case)
    compactness, labels, colors = cv2.kmeans(vectorized, K, None,
                                             criteria, attempts,
                                             cv2.KMEANS_PP_CENTERS)

    colors = colors.astype(np.uint8)

    # Convert back from standard to OpenCV L*a*b after clustering
    # so that it's in a form that OpenCV can work with
    for pixel in colors:
        pixel[0] /= L_SCALE_FACTOR

    # Get the clustered image pixels by:
    # flattening the labels array so it is 1 dimensional
    # then translating each label to its corresponding color
    clustered = colors[labels.flatten()]

    # Now that the image has been reduced to three colors,
    # find out which colors correspond to background, shape, and text.

    # We can find the background color by looking at the color at each corner.
    # The backgrouund will be the most common color at the corners.

    # Reshape the array so it is shaped like an image
    clustered_img = clustered.reshape((img.shape))

    # Get the color at each corner of the image
    corners = [clustered_img[0][0], clustered_img[-1][0],
               clustered_img[0][-1], clustered_img[-1][-1]]

    # Get the number of occurences of each color
    corner_colors, counts = np.unique(corners, return_counts=True, axis=0)

    # Set the background color to the color
    # that appears most often at the corners
    bg_color = corner_colors[np.argmax(counts)]

    # Get the index of the bg_color in the colors list
    # Use np.all to match all three channels of bg_color (r, g, b)
    bg_index = np.all(colors == bg_color, axis=1)

    # Remove the background color from the list.
    # We are now left with just the image and shape color.
    colors = np.delete(colors, bg_index, axis=0)

    # Now just have to differentiate the shape color from the text color.
    # We do this by looking at the number of occurences of each color.
    # The shape should take up more pixels than the text.

    # If colors[0] shows up more than colors[1],
    # then set the text to colors[1] and the shape to colors[0]

    # Use np.all to match all three channels to the color (r, g, b)
    # Use np.sum to count the number of truthy values
    if sum(np.all(clustered == colors[0], axis=1)) >= \
            sum(np.all(clustered == colors[1], axis=1)):
        text_lab = colors[1]
        shape_lab = colors[0]

    # Do the opposite if the reverse is true
    else:
        text_lab = colors[0]
        shape_lab = colors[1]

    # In cases where the shape has a dark border around it (due to shadow,
    # lighting, compression, etc) and the text color is dark, the shape outline
    # may be clustered with the text. To perform accurate color analysis,
    # this border should be removed from the text pixels.

    # Create a mask of all the pixels currently categorized as text pixels
    mask = np.all(clustered == text_lab, axis=1)

    # Reshape the mask to match the image shape
    mask = mask.reshape(img.shape[0:2])

    # Convert the mask to an array of ints, where 255 indicates a text pixel
    # and 0 indicates any other pixel
    mask = mask.astype(np.uint8)*255

    # Here we use the cv2.erode function, which scans the area around a pixel,
    # which is called the kernel. If the kernel contains any pixels of 0 value,
    # then it sets the current pixel to 0. Here, our kernel is a 3x3 square.
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
    mask = cv2.erode(mask, kernel)

    # Perform the masking on the image and reshape it into a list of pixels
    masked = cv2.bitwise_and(img, img, mask=mask)
    masked = masked.reshape((-1, 3))

    # Extract the text pixels by checking for pixels with any non-zero values
    text_pixels = masked[np.any(masked, axis=1)]

    # Calculate the average L, A, and B values.
    text_lab = text_pixels.mean(axis=0)

    # Convert the text and shape colors from LAB to HSV for color matching
    # OpenCV provides no direct way to convert from LAB to HSV,
    # so we must convert from LAB to RGB and then RGB to HSV

    text_hsv = cv2.cvtColor(cv2.cvtColor(np.uint8([[text_lab]]),
                                         cv2.COLOR_LAB2RGB),
                            cv2.COLOR_RGB2HSV)

    shape_hsv = cv2.cvtColor(cv2.cvtColor(np.uint8([[shape_lab]]),
                                          cv2.COLOR_LAB2RGB),
                             cv2.COLOR_RGB2HSV)

    # This dict defines a bounding box for each color in the HSV color space
    # h ranges from (0,179), s ranges from (0,255), v ranges from (0,255)
    # 'color': ((h_min, s_min, v_min), (h_max, s_max, v_max))

    # Note: red is here twice since its hue "wraps around"
    # A second bounding box for blue may need to be added, pending results

    COLOR_RANGES = {
        'white': ((0, 0, 230), (180, 50, 255)),
        'black': ((0, 0, 0), (180, 255, 65)),
        'gray': ((0, 0, 90), (180, 50, 205)),
        'red': ((0, 130, 100), (10, 255, 255)),
        'red': ((165, 130, 100), (180, 255, 255)),
        'blue': ((100, 180, 50), (119, 255, 255)),
        'green': ((45, 100, 60), (85, 255, 255)),
        'yellow': ((25, 60, 200), (35, 255, 255)),
        'purple': ((120, 75, 50), (140, 255, 255)),
        'brown': ((0, 51, 46), (23, 255, 150)),
        'orange': ((11, 140, 155), (30, 255, 255))
    }

    # Now just loop through the color ranges
    # and check if the shape or text color fits within the range

    text_color = ''
    shape_color = ''

    for color in COLOR_RANGES:

        # If the text hsv is in the range of the current color,
        # then set that as the text color
        if cv2.inRange(text_hsv,
                       COLOR_RANGES[color][0], COLOR_RANGES[color][1]):
            text_color = color

        # Do the same with the shape hsv
        if cv2.inRange(shape_hsv,
                       COLOR_RANGES[color][0], COLOR_RANGES[color][1]):
            shape_color = color

    return (text_color, shape_color)
