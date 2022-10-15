import os
import cv2
import numpy as np


def binary_dilation(image):
    # https://github.com/danvk/oldnyc/blob/master/ocr/tess/crop_morphology.py
    kernal_size = int(os.environ.get("DILATION_KERNAL_SIZE"))
    kernal = np.ones((kernal_size, kernal_size), np.uint8)
    dilated_image = image
    """TODO: change repeated dilating an image, ALSO CHANGE MAGIC NUMBER"""
    for i in range(int(2)):
        dilated_image = cv2.dilate(dilated_image, kernal, iterations=i)
    return dilated_image


def crop_rotated_bbox(image, center, size, angle, scale=1):
    # https://jdhao.github.io/2019/02/23/crop_rotated_rectangle_opencv/
    size = (int(size[0]), int(size[1]))
    center = (int(center[0]), int(center[1]))
    width, height = image.shape[0], image.shape[1]
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)
    rotated_image = cv2.warpAffine(image, rotation_matrix, (width, height))
    cropped_image = cv2.getRectSubPix(rotated_image, size, center)
    return cropped_image


def crop_image(image):
    dilated_image = binary_dilation(image)
    contours, _ = cv2.findContours(
        dilated_image,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_SIMPLE)
    bounding_rectangle = cv2.minAreaRect(contours[0])
    box = cv2.boxPoints(bounding_rectangle)
    box = np.int0(box)
    cv2.drawContours(dilated_image, [box], 0, (36, 255, 12), 3)
    center, size, angle = bounding_rectangle[:3]
    cropped_image = crop_rotated_bbox(image, center, size, angle)
    return cropped_image