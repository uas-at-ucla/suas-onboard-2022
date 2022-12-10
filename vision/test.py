import unittest
import cv2
import os

from odlc import tesseract
from odlc import color_detection
from odlc import inference


class AlphanumericModelTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AlphanumericModelTests, self).__init__(*args, **kwargs)
        self.model = inference.Model('/app/odlc/models/alphanumeric_model.pth')
        self.image_path_1 = '/app/images/test/alphanumeric-model-test1.jpg'
        self.image_path_2 = '/app/images/test/tesseract-test4.png'

    def test_alphanumeric_inference_1(self):
        img = cv2.imread(self.image_path_1)
        pred = self.model.detect_boxes(img)
        self.assertEqual(pred.shape[0], 1)
        self.assertTrue(pred[0][0] > 890)
        self.assertTrue(pred[0][0] < 895)
        self.assertTrue(pred[0][1] > 773)
        self.assertTrue(pred[0][1] < 777)
        self.assertTrue(pred[0][2] > 1016)
        self.assertTrue(pred[0][2] < 1020)
        self.assertTrue(pred[0][3] > 865)
        self.assertTrue(pred[0][3] < 870)

    def test_alphanumeric_inference_2(self):
        img = cv2.imread(self.image_path_2)
        pred = self.model.detect_boxes(img)
        self.assertEqual(pred.shape[0], 1)
        self.assertTrue(pred[0][0] > 548)
        self.assertTrue(pred[0][0] < 553)
        self.assertTrue(pred[0][1] > 540)
        self.assertTrue(pred[0][1] < 545)
        self.assertTrue(pred[0][2] > 760)
        self.assertTrue(pred[0][2] < 765)
        self.assertTrue(pred[0][3] > 652)
        self.assertTrue(pred[0][3] < 657)

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
    image_path_1 = '/app/images/test/DJI_01.JPG'
    image_path_2 = '/app/images/test/DJI_02.JPG'
    image_path_3 = '/app/images/test/DJI_03.JPG'
    image_path_4 = '/app/images/test/DJI_04.JPG'
    image_path_5 = '/app/images/test/DJI_05.JPG'
    image_path_6 = '/app/images/test/DJI_06.JPG'
    image_path_7 = '/app/images/test/DJI_07.JPG'
    image_path_8 = '/app/images/test/DJI_08.JPG'
    image_path_9 = '/app/images/test/DJI_09.JPG'
    image_path_10 = '/app/images/test/DJI_10.JPG'
    image_path_11 = '/app/images/test/DJI_11.JPG'
    image_path_12 = '/app/images/test/DJI_12.JPG'
    image_path_13 = '/app/images/test/DJI_13.JPG'

    def test_color_detection_1(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_1)

        self.assertEqual(text_color, 'red')
        self.assertEqual(shape_color, 'blue')

    def test_color_detection_2(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_2)

        self.assertEqual(text_color, 'white')
        self.assertEqual(shape_color, 'black')

    def test_color_detection_3(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_3)

        self.assertEqual(text_color, 'gray')
        self.assertEqual(shape_color, 'yellow')

    def test_color_detection_4(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_4)

        self.assertEqual(text_color, 'green')
        self.assertEqual(shape_color, 'orange')

    def test_color_detection_5(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_5)

        self.assertEqual(text_color, 'orange')
        self.assertEqual(shape_color, 'yellow')

    def test_color_detection_6(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_6)

        self.assertEqual(text_color, 'purple')
        self.assertEqual(shape_color, 'white')

    def test_color_detection_7(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_7)

        self.assertEqual(text_color, 'black')
        self.assertEqual(shape_color, 'orange')

    def test_color_detection_8(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_8)

        self.assertEqual(text_color, 'purple')
        self.assertEqual(shape_color, 'orange')

    def test_color_detection_9(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_9)

        self.assertEqual(text_color, 'white')
        self.assertEqual(shape_color, 'blue')

    def test_color_detection_10(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_10)

        self.assertEqual(text_color, 'blue')
        self.assertEqual(shape_color, 'red')

    def test_color_detection_11(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_11)

        self.assertEqual(text_color, 'blue')
        self.assertEqual(shape_color, 'white')

    def test_color_detection_12(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_12)

        self.assertEqual(text_color, 'red')
        self.assertEqual(shape_color, 'yellow')

    def test_color_detection_13(self):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(self.image_path_13)

        self.assertEqual(text_color, 'orange')
        self.assertEqual(shape_color, 'black')


if __name__ == "__main__":
    unittest.main()
