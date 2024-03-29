import cv2
import numpy as np
from scipy import stats

import time
import util


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


# Return the average distance from the center
# of all nonzero pixels in the image
def avg_dist(mask, center):
    mask_points = np.transpose(mask.nonzero())
    if len(mask_points) == 0:
        return 0

    distance = sum(np.linalg.norm(point - center) for point in mask_points)

    return distance / len(mask_points)


# Perform kmeans clustering to extract the object
# Then cluster repeatedly until text and shape are separated
def get_text_and_shape_mask(image):

    # ---------- EXTRACT OBJECT MASK ---------- #

    blurred = cv2.GaussianBlur(image, (7, 7), 0)
    clustered_img = kmeans(blurred)

    # Extract the background color
    border = np.concatenate((clustered_img[0], clustered_img[-1],
                            clustered_img[:, 0], clustered_img[:, -1]))
    bg_color = stats.mode(border, keepdims=True)[0][0]

    # Exclude the background color
    cluster_mask = np.all(clustered_img != bg_color, axis=2)
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

        shape_mask = np.all(clustered_img == shape_color, axis=2)
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
        shape_mask = np.uint8(shape_mask)

        # Calculate mask center using contour moments for next iteration
        M = cv2.moments(np.uint8(cluster_mask))
        cX = int(M["m10"] / M["m00"])
        cY = int(M["m01"] / M["m00"])
        center = np.array([cY, cX])

        it += 1

    # Logging
    if (it == 5):
        util.error("Error in segmentation.py: WHILE LOOP RUN TOO MAY TIMES")

    util.debug_imwrite(text_mask * 255,
                       f"./images/debug/text-mask-{time.time()}.jpg")
    util.debug_imwrite(shape_mask * 255,
                       f"./images/debug/shape-mask-{time.time()}.jpg")

    return text_mask, shape_mask
