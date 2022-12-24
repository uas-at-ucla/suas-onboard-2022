"""
Light wrapper around Tesseract OCR model
"""

import pytesseract
import cv2
import os
from odlc.cropper import crop_shape, crop_image_alpha
import numpy as np
from functools import reduce

# Assumes that the cropped image contains a single alphanumeric character
# Takes the image, deskews, binarizes, pads image
# Outputs a list of tuples containing a predicted character and confidence
# Ideally, the maximum confidence character is the true character, but
# if that character does not match any of the alphanumeric targets,
# assume highest confidence character which does
# @param cropped_image: cropped image filepath
# @return list containing tuples of characters and our confidence

def noise_removal(image):
    #https://github.com/wjbmattingly/ocr_python_textbook/blob/main/02_02_working%20with%20opencv.ipynb
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=2)
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.erode(image, kernel, iterations=2)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.medianBlur(image, 3)
    return (image)

def thin_font(image):
    image = cv2.bitwise_not(image)
    kernel = np.ones((2,2),np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.bitwise_not(image)
    return (image)

def thick_font(image):
    image = cv2.bitwise_not(image)
    kernel = np.ones((2,2),np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    image = cv2.bitwise_not(image)
    return (image)

def filter_contour(contours, image_width, image_height):
    # TODO: automate process, change values
    #pick the largest 30
    if(len(contours) > 30):
        contours = list(sorted(contours, key= lambda contour: cv2.contourArea(contour), reverse=True))
        contours = contours[:30]

    image_area = (image_height * image_width)

    new_contours = list(filter(lambda contour: cv2.contourArea(contour) / image_area > 0.03 and cv2.contourArea(contour) / image_area < 0.5, contours))
    return new_contours

def extract_images_from_contour(image, contours):
    output = []
    image_height, image_width = image.shape[:2]
    for contour in contours:
        x,y,w,h = cv2.boundingRect(contour)
        #TODO: add border
        padding = 0
        y -= padding
        h += 2 * padding
        x -= padding
        w += 2 * padding

        #making sure everything is in bounds still
        y = max(y, 0)
        x = max(x, 0)
        h = min(h, image_height - 1)
        w = min(w, image_width - 1)

        new_image = image[y:y+h, x:x+w]
        output.append(new_image)
    return output


def cropped_images_to_binary(image):
    #TODO: k means clustering as a form of binarization, test variables
    #The assumption for this function is that image is an image that
    #primarily contains two colors, the background and letter color
    #clustering is then possible as opposed to your normal binarization
    flattened_image = np.float32(image.reshape((-1, 3)))

    MAX_ITER = 10
    EPS = 0.85
    k = 2
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, MAX_ITER, EPS)
    retval, labels, centers = cv2.kmeans(flattened_image, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS) 
    image_height, image_width = image.shape[:2]
    labels = labels.reshape((image_height, image_width))
    labels *= 255
    labels = np.array(labels, dtype=np.uint8)
    return labels

def generate_predictions(image):
    output = []
    config_str = '--psm 10 -c tessedit_char_whitelist'
    config_str += '=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    height, width = image.shape[:2]
    center = (width // 2, height // 2)
    rotation_matrix_ninety = cv2.getRotationMatrix2D(center, 90, 1.0)
    for _ in range(0, 4):
        # get tesseract data from the image
        # we are interested in the recognized letter and its confidence
        data = pytesseract.image_to_data(
            image,
            config=config_str,
            output_type="data.frame"
        )
        # using pandas, get the row with confidence greater than 0
        letter_row = data[data["conf"] > 0]
        # reset index of pandas series
        letter_row = letter_row.reset_index()
        # get the recognized letter and its confidence, add to output list
        if not letter_row.empty:
            letter = letter_row["text"][0]
            confidence = letter_row["conf"][0]
            output.append((letter, confidence))

        # rotate image by 90 degrees for next pass
        image = cv2.warpAffine(
            image,
            rotation_matrix_ninety,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE)
    return output

def get_matching_text(image):
    og_image = image.copy()
    #TODO: automatted contrast correcting
    # between 1-3
    contrast_multiplier = 2
    # between 0 - 100
    brightness_multiplier = 0
    image = cv2.convertScaleAbs(image, alpha=contrast_multiplier, beta=brightness_multiplier)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(image, (5, 5), 0)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-ocr_blur.png', image)

    image = cv2.adaptiveThreshold(image,255,cv2.ADAPTIVE_THRESH_GAUSSIAN_C,\
             cv2.THRESH_BINARY,7,1)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-ocr_post_threshold.png', image)
    
    image = noise_removal(image)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-noise_removed.png', image)

    thick_font_image = thick_font(image)
    image = thin_font(image)

    image = noise_removal(image)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-noise_thin.png', image)
        cv2.imwrite('./images/debug/img-noise_thick.png', thick_font_image)

    contours, _ = cv2.findContours(image, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    if os.getenv("DEBUG"):
        all_contours_image = cv2.drawContours(og_image.copy(), contours, -1, (0,255,0), 3)
        cv2.imwrite('./images/debug/img-all_contours.png', all_contours_image)

    image_height = image.shape[0]
    image_width = image.shape[1]
    
    if os.getenv("DEBUG"):
        print("PRE FILTER: ", len(contours))
    
    contours = filter_contour(contours, image_height, image_width)
    
    if os.getenv("DEBUG"):
        print("POST FILTER: ", len(contours))
        filtered_contour = cv2.drawContours(og_image.copy(), contours, -1, (0,255,0), 3)
        cv2.imwrite('./images/debug/img-filtered_contours.png', filtered_contour)
    
    cropped_images = extract_images_from_contour(og_image, contours)
    cropped_images = list(map(lambda crop_image: cropped_images_to_binary(crop_image), cropped_images))
    if os.getenv("DEBUG"):
        for index, crop_image in enumerate(cropped_images):
            cv2.imwrite('./images/debug/crops/{}.png'.format(index), crop_image)
    predictions = list(map(lambda crop_image: generate_predictions(crop_image), cropped_images))
    print(predictions)
    predictions = reduce(lambda prediction_a, prediction_b: prediction_a + prediction_b, predictions)
    predictions = sorted(predictions, key=lambda prediction: prediction[1], reverse=True)

    return predictions


# TODO: unit testing for various characters, background colors/shapes, add
# noise, distortions, rotations
