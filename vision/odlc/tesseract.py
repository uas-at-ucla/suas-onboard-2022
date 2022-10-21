"""
Light wrapper around Tesseract OCR model
"""

import pytesseract
import cv2
import os
from odlc.cropper import crop_shape, crop_image_alpha

# Assumes that the cropped image contains a single alphanumeric character
# Takes the image, deskews, binarizes, pads image
# Outputs a list of tuples containing a predicted character and confidence
# Ideally, the maximum confidence character is the true character, but
# if that character does not match any of the alphanumeric targets,
# assume highest confidence character which does
# @param cropped_image: cropped image filepath
# @return list containing tuples of characters and our confidence


def get_matching_text(cropped_img):
    image = cv2.imread(cropped_img)  # reads image
    image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)  # grayscale

    # Binarizes text such that foreground becomes 255, background becomes 0
    # Binarization is conducted via openCV THRESH_OTSU (Otsu's method)
    image = cv2.threshold(image, 0, 255,
                          cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]

    # add padding to image such that rotation can occur without cutting out
    # image since minAreaRect can return negative indices in some cases

    width, height = image.shape[:2]  # get height, width of image

    # Given that the paper is white, the image we receive contains
    # a background, a white rectangle (could be rotated),
    # and the letter. Once we binarize, each non-black pixel
    # in the background should be made black
    # Thus, we loop through each pixel in
    # the image and until we find our first black, we set
    # every pixel up to that point to black
    # this leaves us with the desired image with white text
    # and a black background
    for h in range(0, height):
        for w in range(0, width):
            if (image[w][h] != 0):
                image[w][h] = 0
            else:
                break
        for w in reversed(range(width)):
            if (image[w][h] != 0):
                image[w][h] = 0
            else:
                break

    # testing the case when we get a really good crop
    # then the hierachal contour selection isn't needed
    config_str = '--psm 10 -c tessedit_char_whitelist'
    config_str += '=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
    good_crop = crop_image_alpha(image)

    width, height = good_crop.shape[:2]
    center = (width // 2, height // 2)  # compute the approximate center
    # After image is rotated, there are 4 cases: text is right side up
    # text is rotated 90 degrees, 180 degrees, or 270 degrees

    rotation_matrix_ninety = cv2.getRotationMatrix2D(center, 90, 1.0)
    output = []

    for _ in range(0, 4):

        # get tesseract data from the image
        # we are interested in the recognized letter and its confidence
        config_str = '--psm 10 -c tessedit_char_whitelist'
        config_str += '=ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890'
        data = pytesseract.image_to_data(
            good_crop,
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
        good_crop = cv2.warpAffine(
            good_crop,
            rotation_matrix_ninety,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE)
    # TODO: do the other one based on confidence instead
    image = crop_shape(image)

    # Returns coordinates of all white pixels (text pixels)
    # OpenCV provides a method which returns the minimum area rectangle
    # containing the coordinates. The final element of this Box2D object
    # is the angle of the rectangle, hence we assign that to angle
    # get the height and width of the image
    width, height = image.shape[:2]
    center = (width // 2, height // 2)  # compute the approximate center
    # After image is rotated, there are 4 cases: text is right side up
    # text is rotated 90 degrees, 180 degrees, or 270 degrees

    rotation_matrix_ninety = cv2.getRotationMatrix2D(center, 90, 1.0)

    # Save the preprocessed image if we are debugging
    if os.getenv('DEBUG'):
        cv2.imwrite('./img.png', image)

    # we check if a letter is detected in every case (right way up, upside
    # down, 90 degrees left, 90 degrees right)
    for i in range(0, 4):

        # get tesseract data from the image
        # we are interested in the recognized letter and its confidence
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
        image = cv2.warpAffine(
            image,
            rotation_matrix_ninety,
            (width, height),
            flags=cv2.INTER_CUBIC,
            borderMode=cv2.BORDER_REPLICATE)

    # make sure output list of tuples is sorted in
    # decreasing order by confidence
    output = sorted(output, key=lambda x: x[1], reverse=True)

    return output


# TODO: unit testing for various characters, background colors/shapes, add
# noise, distortions, rotations
