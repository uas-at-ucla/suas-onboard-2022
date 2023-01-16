import numpy as np
import cv2

def noise_removal(image):
    """Using dilation, erosion, bluring and
       morphology, remove small noise grains

    Args:
        image (cv2 image):

    Returns:
        cv2 image:
    """
    # taken from:
    # https://github.com/wjbmattingly/ocr_python_textbook/blob/main/02_02_working%20with%20opencv.ipynb
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    kernel = np.ones((1, 1), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.morphologyEx(image, cv2.MORPH_CLOSE, kernel)
    image = cv2.medianBlur(image, 3)
    return (image)


def thin_font(image):
    """Enlargens dark pixels via erosion,
       making text "seem" thinner

    Args:
        image (cv2 image):

    Returns:
        cv2 image:
    """
    image = cv2.bitwise_not(image)
    kernel = np.ones((2, 2), np.uint8)
    image = cv2.erode(image, kernel, iterations=1)
    image = cv2.bitwise_not(image)
    return (image)


def thick_font(image):
    """Enlargens white pixels via dilation,
       making text "seem" thicker

    Args:
        image (cv2 image):

    Returns:
        cv2 image:
    """
    image = cv2.bitwise_not(image)
    kernel = np.ones((2, 2), np.uint8)
    image = cv2.dilate(image, kernel, iterations=1)
    image = cv2.bitwise_not(image)
    return (image)


def filter_contour(contours, image_width, image_height):
    """Filter the largest 5 contours and those whose area
    is more than 3% the image and less than 50% the image

    Args:
        contours (cv2 contours):
        image_width (int):
        image_height (int):

    Returns:
        list: list of filtered contours
    """
    # TODO: automate process, change values
    # pick the largest 10 contours
    if len(contours) > 10:
        contours = list(sorted(
            contours,
            key=lambda contour: cv2.contourArea(contour),
            reverse=True))
        contours = contours[:10]

    image_area = (image_height * image_width)

    # find the contour box area
    def internal_filter(contour):
        _, _, h, w = cv2.boundingRect(contour)
        print(h * w / image_area)
        if h * w / image_area < 0.03:
            return False
        return True

    new_contours = list(filter(
        internal_filter,
        contours))
    return new_contours


def extract_images_from_contour(image, contours):
    """Given a contour, return the image inside the
       rectangular bounding box of each contour

    Args:
        image (cv2 image): the in-color, original image without modifcations
        contours (cv2 contours):

    Returns:
        list: a list of cropped images
    """
    output = []
    image_height, image_width = image.shape[:2]
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # TODO: confirm whether image bordering is needed
        padding = 0
        y -= padding
        h += 2 * padding
        x -= padding
        w += 2 * padding

        # making sure everything is in bounds still
        y = max(y, 0)
        x = max(x, 0)
        h = min(h, image_height - 1)
        w = min(w, image_width - 1)

        new_image = image[y:y+h, x:x+w]
        output.append(new_image)
    return output


def distance_from_pixel(pixel_a, pixel_b):
    """Returns the square distance of one pixel to another

    Args:
        pixel_a (float tuple): RGB values
        pixel_b (float tuple): RGB values

    Returns:
        float: the square distance
    """
    return (pixel_a[0] - pixel_b[0]) ** 2 + (pixel_a[1] - pixel_b[1]) ** 2 + \
           (pixel_a[2] - pixel_b[2]) ** 2


def cropped_images_to_binary(image, mean_pixel_value):
    """Binarizes an image using k-means clustering, where k = 2

    Args:
        image (cv2 image):
        mean_pixel_value (float tuple): an RGB tuple where the
        values equal to the average values of the shape contour,
        this is used to assign the appropriate label (either 0 or 1) to the
        inside letter

    Returns:
        cv2 image: binarized cv2 image
    """
    # TODO: test variables, and change values
    # The assumption for this function is that image is an image that
    # primarily contains two colors, the background and letter color
    # clustering is then possible as opposed to your normal binarization
    flattened_image = np.float32(image.reshape((-1, 3)))

    MAX_ITER = 10
    EPS = 0.85
    k = 2
    criteria = (
        cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER,
        MAX_ITER,
        EPS)

    _, labels, centers = cv2.kmeans(
        flattened_image,
        k,
        None,
        criteria,
        10,
        cv2.KMEANS_RANDOM_CENTERS)
    image_height, image_width = image.shape[:2]
    mean_pixel_value = mean_pixel_value[:3]
    labels = labels.reshape((image_height, image_width))
    labels *= 255
    if distance_from_pixel(centers[0], mean_pixel_value) > \
       distance_from_pixel(centers[1], mean_pixel_value):
        labels = 255 - labels
    labels = np.array(labels, dtype=np.uint8)
    return labels


def image_with_border(image):
    """Returns a cv2 image with either a black
       or white border depending on the average of the
       corners of the image

    Args:
        image (cv2 image):

    Returns:
        cv2 image: original image with border
    """
    # get average of 4 corners
    height, width = image.shape[:2]
    corners = int(image[0][0])
    corners += int(image[0][width-1])
    corners += int(image[height-1][0])
    corners += int(image[height-1][width-1])
    corners /= 4

    # check if corners is closer to white than black
    white = 255
    black = 0
    if corners < 255 / 2:
        corners = black
    else:
        corners = white

    bordersize = 10
    image = cv2.copyMakeBorder(
        image,
        top=bordersize,
        bottom=bordersize,
        left=bordersize,
        right=bordersize,
        borderType=cv2.BORDER_CONSTANT,
        value=corners
    )

    return image


def average_color_contour(contour, image):
    """Returns average pixel values of contour

    Args:
        contour (cv2 contour): _description_
        image (cv2 image): _description_

    Returns:
        float tuple: (R value, G value, B vavue)
    """
    mask = np.zeros(image.shape[:2], np.uint8)
    cv2.drawContours(mask, [contour], 0, 255, -1)
    mean = cv2.mean(image, mask=mask)
    return mean
