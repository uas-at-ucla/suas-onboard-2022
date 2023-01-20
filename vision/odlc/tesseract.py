"""
Light wrapper around Tesseract OCR model
"""

import pytesseract
import cv2
import os
from functools import reduce
from odlc.image_processing import noise_removal, thick_font, \
    filter_contour, extract_images_from_contour, cropped_images_to_binary, \
    image_with_border, average_color_contour


def generate_predictions(image):
    output = []
    image = image_with_border(image)

    for _ in range(0, 4):
        # get tesseract data from the image
        # we are interested in the recognized letter and its confidence
        if os.getenv("DEBUG"):
            cv2.imwrite("./images/debug/img-rotate{}.png".format(_), image)
        config_str = '--psm 10 -c tessedit_char_whitelist'
        config_str += '=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
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
        image = cv2.rotate(image, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return output


def combine_similar_predictions(predictions):
    seen_characters = {}
    for prediction in predictions:
        if prediction[0] in seen_characters:
            seen_characters[prediction[0]] += prediction[1]
        else:
            seen_characters[prediction[0]] = prediction[1]
    return list(seen_characters.items())

# Outputs a list of tuples containing a predicted character and confidence
# Ideally, the maximum confidence character is the true character, but
# if that character does not match any of the alphanumeric targets,
# assume highest confidence character which does
# @param cropped_image: cropped image filepath
# @return list containing tuples of characters and our confidence


def get_matching_text(image):
    og_image = image.copy()
    # TODO: automatted contrast correcting
    # between 1-3
    contrast_multiplier = 2
    # between 0 - 100
    brightness_multiplier = 0
    image = cv2.convertScaleAbs(image, alpha=contrast_multiplier,
                                beta=brightness_multiplier)

    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    image = cv2.GaussianBlur(image, (5, 5), 0)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-ocr_blur.png', image)

    image = cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                  cv2.THRESH_BINARY, 7, 1)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-ocr_post_threshold.png', image)

    image = noise_removal(image)

    image = thick_font(image)

    if os.getenv("DEBUG"):
        cv2.imwrite('./images/debug/img-noise_removed.png', image)

    contours, _ = cv2.findContours(image, cv2.RETR_TREE,
                                   cv2.CHAIN_APPROX_SIMPLE)

    if os.getenv("DEBUG"):
        all_contours_image = cv2.drawContours(og_image.copy(), contours, -1,
                                              (0, 255, 0), 3)
        cv2.imwrite('./images/debug/img-all_contours.png', all_contours_image)

    image_height = image.shape[0]
    image_width = image.shape[1]

    contours = filter_contour(contours, image_height, image_width)

    if os.getenv("DEBUG"):
        filtered_contour = cv2.drawContours(og_image.copy(), contours, -1,
                                            (0, 255, 0), 3)
        cv2.imwrite('./images/debug/img-filtered_contours.png',
                    filtered_contour)

    mean_contour_pixel_values = list(map(
        lambda contour: average_color_contour(contour, og_image),
        contours))

    # og_image = cv2.cvtColor(og_image, cv2.COLOR_BGR2GRAY)
    cropped_images = extract_images_from_contour(og_image, contours)
    k_means_images = []
    # k_means_images = cropped_images
    for index, crop_image in enumerate(cropped_images):
        k_means_images.append(cropped_images_to_binary(
            crop_image,
            mean_contour_pixel_values[index]))

    if os.getenv("DEBUG"):
        for index, crop_image in enumerate(k_means_images):
            cv2.imwrite('./images/debug/crops/{}.png'.format(index),
                        crop_image)
    predictions = list(map(
        lambda crop_image: generate_predictions(crop_image),
        k_means_images))
    predictions = reduce(
        lambda prediction_a, prediction_b: prediction_a + prediction_b,
        predictions)
    predictions = combine_similar_predictions(predictions)
    predictions = sorted(
        predictions,
        key=lambda prediction: prediction[1], reverse=True)
    return predictions


# TODO: unit testing for various characters, background colors/shapes, add
# noise, distortions, rotations
