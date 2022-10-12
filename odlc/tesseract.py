"""
Light wrapper around Tesseract OCR model
"""

import pytesseract
import numpy as np
import cv2
import os

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
    horiz_padding = width // 4  # set vertical padding
    vertical_padding = height // 4  # set horizontal padding
    BLACK = [0, 0, 0]

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
            if (image[h][w] != 0):
                image[h][w] = 0
            else:
                break
        for w in reversed(range(0, width)):
            if (image[h][w] != 0):
                image[h][w] = 0
            else:
                break

    # add black padding with horiz_padding on left, right
    # and vertical_padding on top, bottom
    image = cv2.copyMakeBorder(image, vertical_padding, vertical_padding,
                               horiz_padding, horiz_padding,
                               cv2.BORDER_CONSTANT, value=BLACK)

    # recompute width, height of image for later use
    width, height = image.shape[:2]
    # Returns coordinates of all white pixels (text pixels)
    locs = np.column_stack(np.where(image > 0))

    # OpenCV provides a method which returns the minimum area rectangle
    # containing the coordinates. The final element of this Box2D object
    # is the angle of the rectangle, hence we assign that to angle

    rect = cv2.minAreaRect(locs)
    angle = - rect[-1]  # set rotation angle to the negative of the angle
    width, height = image.shape[:2]  # get the height and width of the image
    center = (width // 2, height // 2)  # compute the approximate center
    rotation_matrix = cv2.getRotationMatrix2D(center, angle, 1.0)

    image = cv2.warpAffine(image, rotation_matrix, (width, height),
                           flags=cv2.INTER_CUBIC,
                           borderMode=cv2.BORDER_REPLICATE)  # apply rotation
    image = cv2.bitwise_not(image)  # invert image to get black text on white

    # After image is rotated, there are 4 cases: text is right side up
    # text is rotated 90 degrees, 180 degrees, or 270 degrees
    rotation_matrix_ninety = cv2.getRotationMatrix2D(center, 90, 1.0)

    output = []

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
        data = pytesseract.image_to_data(image, config=config_str,
                                         output_type="data.frame")
        # using pandas, get the row with confidence greater than 0
        letter_row = data[data["conf"] > 0]
        letter_row = letter_row.reset_index()  # reset index of pandas series

        # get the recognized letter and its confidence, add to output list
        if not letter_row.empty:
            letter = letter_row["text"][0]
            confidence = letter_row["conf"][0]
            output.append((letter, confidence))

        # rotate image by 90 degrees for next pass
        image = cv2.warpAffine(image, rotation_matrix_ninety, (width, height),
                               flags=cv2.INTER_CUBIC,
                               borderMode=cv2.BORDER_REPLICATE)

    # make sure output list of tuples is sorted in
    # decreasing order by confidence
    output = sorted(output, key=lambda x: x[1], reverse=True)

    return output


# TODO: unit testing for various characters, background colors/shapes, add
# noise, distortions, rotations
