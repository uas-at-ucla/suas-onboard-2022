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


def crop_image_alpha(image):
    dilated_image = image
    for _ in range(2):
        dilated_image = binary_dilation(dilated_image)
    contours, _ = cv2.findContours(
        dilated_image,
        cv2.RETR_EXTERNAL,
        cv2.CHAIN_APPROX_NONE)
    if len(contours) == 0:
        return image
    # select the target contour based on largest contour
    contour_areas = [cv2.contourArea(x) for x in contours]
    target_index = contour_areas.index(max(contour_areas))

    bounding_rectangle = cv2.minAreaRect(contours[target_index])
    center, size, angle = bounding_rectangle[:3]
    cropped_image = crop_rotated_bbox(image, center, size, angle)
    return cropped_image


# returns the largest detected shape, removing noise, etc
def crop_shape(image):
    dilated_image = image
    for _ in range(5):
        dilated_image = binary_dilation(dilated_image)
    # https://stackoverflow.com/questions/41576815/drawing-contours-using-cv2-approxpolydp-in-python
    contours, hierarchy = cv2.findContours(
        dilated_image,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_NONE
    )

    # use cv2 hierarchy structure
    # because cv2.findContours always returns it in
    # a proper hierarchal structure, the target index is always the one
    # two layers deep from root
    # basic theory explaantion:
    # https://stackoverflow.com/questions/11782147/python-opencv-contour-tree-hierarchy-structure
    # TODO: add better exit condition
    PARENT_INDEX = 3
    target_index = -1
    hierarchy = hierarchy[0]
    for index, object in enumerate(hierarchy):
        # check the first and then the second parent
        object_parent = object[PARENT_INDEX]
        if object_parent != -1:
            # check grand parent
            grand_parent = hierarchy[object_parent][PARENT_INDEX]
            if grand_parent != -1:
                target_index = index
                break
    # TODO: write test case if target index = -1
    target_contour = contours[target_index]
    epsilon = 0.1*cv2.arcLength(target_contour, True)
    approximated_contour = cv2.approxPolyDP(target_contour, epsilon, True)
    x, y, h, w = cv2.boundingRect(approximated_contour)

    # TODO: redo padding to initial crop
    horizontal_padding = w // 4
    vertical_padding = h // 4

    # this image is undilated
    cropped_image = image[y:y+h, x:x+w]

    # add padding
    cropped_image = cv2.copyMakeBorder(
        cropped_image,
        vertical_padding,
        vertical_padding,
        horizontal_padding,
        horizontal_padding,
        cv2.BORDER_CONSTANT,
        value=[0, 0, 0])

    final_image = crop_image_alpha(cropped_image)

    return final_image
