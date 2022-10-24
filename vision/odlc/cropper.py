import os
import cv2
import numpy as np

PARENT_INDEX = 3


def binary_dilation(image):
    # https://github.com/danvk/oldnyc/blob/master/ocr/tess/crop_morphology.py
    kernal_size = int(os.environ.get("DILATION_KERNAL_SIZE"))
    # n x n full kernal
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
    cropped_image = cv2.getRectSubPix(image, size, center)

    width, height = cropped_image.shape[:2]
    # add padding
    cropped_image = cv2.copyMakeBorder(
        cropped_image,
        height//4,
        height//4,
        width//4,
        width//4,
        cv2.BORDER_CONSTANT
    )

    center = (cropped_image.shape[0]//2, cropped_image.shape[1]//2)
    width, height = cropped_image.shape[:2]

    # rotate cropped images
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, scale)
    rotated_image = cv2.warpAffine(
        cropped_image,
        rotation_matrix,
        (width, height)
    )

    return rotated_image


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
    return cropped_image, center


def crop_image_multiple_targets(image):
    dilated_image = image
    for _ in range(5):
        dilated_image = binary_dilation(dilated_image)
    contours, hierarchy = cv2.findContours(
        dilated_image,
        cv2.RETR_TREE,
        cv2.CHAIN_APPROX_NONE
    )
    contours = [contours[i] for i in objects_lookup_distance(hierarchy)]
    dilated_image = cv2.cvtColor(dilated_image, cv2.COLOR_GRAY2RGB)

    image = cv2.cvtColor(image, cv2.COLOR_GRAY2RGB)

    # crop shape
    results = []
    for contour in contours:
        rectangle = cv2.minAreaRect(contour)
        center, size, angle = rectangle[:3]
        cropped_shape = crop_rotated_bbox(image, center, size, angle)
        results.append((cropped_shape, center))

    return results


def objects_lookup_distance(hierachy, lookup_distance=2):
    hierachy = hierachy[0]
    results = []
    for index, object in enumerate(hierachy):
        lookup_flag = True
        current = object
        for _ in range(lookup_distance):
            if current[PARENT_INDEX] != -1:
                current = hierachy[current[PARENT_INDEX]]
            else:
                lookup_flag = False
        # check if the third lookup_distance is -1
        if current[PARENT_INDEX] != -1:
            lookup_flag = False
        if lookup_flag:
            results.append(index)
    return results
