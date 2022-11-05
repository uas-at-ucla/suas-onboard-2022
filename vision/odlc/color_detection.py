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
# by counting the occurences of each color.


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

    # Convert to RGB and return values
    text_rgb = cv2.cvtColor(np.uint8([[text_lab]]), cv2.COLOR_LAB2RGB)
    shape_rgb = cv2.cvtColor(np.uint8([[shape_lab]]), cv2.COLOR_LAB2RGB)

    return (text_rgb, shape_rgb)
