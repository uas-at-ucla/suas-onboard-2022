import unittest

from odlc import tesseract
from odlc import color_detection

import cv2


class TesseractTests(unittest.TestCase):
    image_path_1 = '/app/images/test/tesseract-test1.png'
    image_path_2 = '/app/images/test/tesseract-test2.png'
    image_path_3 = '/app/images/test/tesseract-test3.png'
    image_path_4 = '/app/images/test/tesseract-test4.png'

    def test_tesseract_image_1(self):
        det = tesseract.get_matching_text(self.image_path_1)
        print(det)
        self.assertEqual(det[0][0], "A")

    def test_tesseract_image_2(self):
        det = tesseract.get_matching_text(self.image_path_2)
        self.assertEqual(det[0][0], "A")

    def test_tesseract_image_3(self):
        det = tesseract.get_matching_text(self.image_path_3)
        self.assertEqual(det[0][0], "A")

    def test_tesseract_image_4(self):
        det = tesseract.get_matching_text(self.image_path_4)
        print(det)
        self.assertEqual(det[0][0], "A")


class ColorDetectionTests(unittest.TestCase):
    image_path_1 = 'images/test/color-detection-test-1.png'
    image_path_2 = 'images/test/color-detection-test-2.png'

    def test_color_detection_1(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_1)

        # should be white
        self.assertTrue(cv2.inRange(text_color,
                                    (230, 230, 230), (255, 255, 255)))

        # color picker gave me rgb(72, 62, 124)
        self.assertTrue(cv2.inRange(shape_color,
                                    (52, 42, 104), (92, 82, 144)))

    def test_color_detection_2(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_2)

        # color picker gave me rgb(95, 38, 44)
        self.assertTrue(cv2.inRange(text_color,
                                    (75, 18, 24), (115, 58, 64)))

        # color picker gave me rgb(236, 132, 24)
        self.assertTrue(cv2.inRange(shape_color,
                                    (216, 112, 4), (256, 152, 44)))


if __name__ == "__main__":
    unittest.main()
