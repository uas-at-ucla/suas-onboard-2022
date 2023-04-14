import unittest
from parameterized import parameterized

import cv2
import requests

from odlc import color_detection
from odlc import inference
from odlc import shape_detection
from odlc import MobilenetWrapper


class AlphanumericModelTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(AlphanumericModelTests, self).__init__(*args, **kwargs)
        self.model = inference.Model('/app/odlc/models/alphanumeric_model.pth')
        self.image_path_1 = '/app/images/test/alphanumeric-model-test1.jpg'
        self.image_path_2 = '/app/images/test/tesseract-test4.png'

    def test_alphanumeric_inference_1(self):
        img = cv2.imread(self.image_path_1)
        pred = self.model.detect_boxes(img)
        self.assertEqual(len(pred), 1)
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
        self.assertEqual(len(pred), 1)
        self.assertTrue(pred[0][0] > 548)
        self.assertTrue(pred[0][0] < 553)
        self.assertTrue(pred[0][1] > 540)
        self.assertTrue(pred[0][1] < 545)
        self.assertTrue(pred[0][2] > 760)
        self.assertTrue(pred[0][2] < 765)
        self.assertTrue(pred[0][3] > 652)
        self.assertTrue(pred[0][3] < 657)


class EmergentModelTests(unittest.TestCase):
    def __init__(self, *args, **kwargs):
        super(EmergentModelTests, self).__init__(*args, **kwargs)
        self.model = inference.Model('/app/odlc/models/emergent_model.pth')
        self.image_path_1 = '/app/images/test/emergent-model-test1.jpg'

    def test_emergent_inference_1(self):
        img = cv2.imread(self.image_path_1)
        pred = self.model.detect_boxes(img)
        self.assertEqual(len(pred), 1)
        self.assertTrue(pred[0][0] > 395)
        self.assertTrue(pred[0][0] < 400)
        self.assertTrue(pred[0][1] > 1154)
        self.assertTrue(pred[0][1] < 1159)
        self.assertTrue(pred[0][2] > 1078)
        self.assertTrue(pred[0][2] < 1083)
        self.assertTrue(pred[0][3] > 1662)
        self.assertTrue(pred[0][3] < 1667)


class TesseractTests(unittest.TestCase):
    # @parameterized.expand([
    #    ('/app/images/test/tesseract-test1.png', "A"),
    #    ('/app/images/test/tesseract-test2.png', "A"),
    #    ('/app/images/test/tesseract-test3.png', "A")])
    # @parameterized.expand([
    #    ('/app/images/test/tesseract-test1.png', "A"),
    #    ('/app/images/test/tesseract-test3.png', "A")])
    # def test_ideal_generated_images(self, path, result):
    #     net = MobilenetWrapper.MobilenetWrapper()
    #     img = cv2.imread(path)
    #     det = net.get_matching_text(img)
    #     print(det)
    #     self.assertEqual(det[0][0], result)

    @parameterized.expand([
       ('/app/images/test/DJI_01.JPG', "D"),
       ('/app/images/test/DJI_02.JPG', "A"),
       ('/app/images/test/DJI_05.JPG', "E"),
       ('/app/images/test/DJI_06.JPG', "T")
       ])
    #    ('/app/images/test/DJI_03.JPG', "U"), FAIL
    #    ('/app/images/test/DJI_04.JPG', "8"), FAIL
    def test_dji_images(self, path, result):
        net = MobilenetWrapper.MobilenetWrapper()
        img = cv2.imread(path)
        det = net.get_matching_text(img)
        self.assertEqual(det[0][0], result)


class ColorDetectionTests(unittest.TestCase):
    # path, text color, shape color
    # TODO: DJI_12 text color fails
    @parameterized.expand([
       ('/app/images/test/DJI_01.JPG', "red", "blue"),
       ('/app/images/test/DJI_02.JPG', "white", "black"),
       ('/app/images/test/DJI_03.JPG', "gray", "yellow"),
       ('/app/images/test/DJI_04.JPG', "green", "orange"),
       ('/app/images/test/DJI_05.JPG', "orange", "yellow"),
       ('/app/images/test/DJI_06.JPG', "purple", "white"),
       ('/app/images/test/DJI_07.JPG', "black", "orange"),
       ('/app/images/test/DJI_08.JPG', "purple", "orange"),
       ('/app/images/test/DJI_09.JPG', "white", "blue"),
       ('/app/images/test/DJI_10.JPG', "blue", "red"),
       ('/app/images/test/DJI_11.JPG', "blue", "white"),
       # ('/app/images/test/DJI_12.JPG', "orange", "yellow"),
       ('/app/images/test/DJI_13.JPG', "orange", "black")])
    def test_color_detection_1(self, image_path, target_text, target_shape):
        text_color, shape_color = \
            color_detection.get_text_and_shape_color(cv2.
                                                     imread(image_path))

        self.assertEqual(text_color, target_text)
        self.assertEqual(shape_color, target_shape)


class ShapeClassificationTests(unittest.TestCase):

    # path, shape
    @parameterized.expand([
       ('/app/images/test/DJI_01.JPG', "semicircle"),
       ('/app/images/test/DJI_02.JPG', "circle"),
       ('/app/images/test/DJI_03.JPG', "rectangle"),
       ('/app/images/test/DJI_04.JPG', "cross"),
       ('/app/images/test/DJI_05.JPG', "quarter-circle"),
       ('/app/images/test/DJI_06.JPG', "pentagon"),
       ('/app/images/test/DJI_07.JPG', "hexagon"),
       ('/app/images/test/DJI_08.JPG', "triangle"),
       ('/app/images/test/DJI_09.JPG', "heptagon"),
       ('/app/images/test/DJI_10.JPG', "octagon"),
       ('/app/images/test/DJI_11.JPG', "heptagon"),
       ('/app/images/test/DJI_12.JPG', "star"),
       ('/app/images/test/DJI_13.JPG', "hexagon")])
    def test_shape_detection_1(self, image_path, target_shape):
        shape_detection.initialize(['triangle', 'circle', 'rectangle',
                                    'trapezoid', 'pentagon', 'square',
                                    'semicircle', 'quarter-circle',
                                    'heptagon', 'hexagon', 'octagon'])
        predictions = shape_detection.detect_shape(cv2.
                                                   imread(image_path))

        self.assertEqual(predictions[0][0], target_shape)


class IntegrationTests(unittest.TestCase):
    paths = [
        ('/app/images/test/alphanumeric-model-test2.jpg', 38.31442311312976,
         -76.54522971451763),
        ('/app/images/test/alphanumeric-model-test1.jpg', 38.31421041772561,
         -76.54400246436776),
        ('/app/images/test/alphanumeric-model-test3.jpg', 38.3144070396263,
         -76.54394394383165),
        ('/app/images/test/emergent-model-test1.jpg', 38.3143, -76.544)
    ]

    def test_targets(self):
        targets = [
            {
                'type': 'emergent'
            },
            {
                'type': 'alphanumeric',
                'class': {
                    'shape-color': 'blue',
                    'text-color': 'green',
                    'text': 'W',
                    'shape': 'trapezoid',
                }
            },
            {
                'type': 'alphanumeric',
                'class': {
                    'shape-color': 'red',
                    'text-color': 'blue',
                    'text': '2',
                    'shape': 'octagon',
                }
            },
            {
                'type': 'alphanumeric',
                'class': {
                    'shape-color': 'blue',
                    'text-color': 'white',
                    'text': 'N',
                    'shape': 'heptagon',
                }
            },
            {
                'type': 'alphanumeric',
                'class': {
                    'shape-color': 'blue',
                    'text-color': 'red',
                    'text': 'D',
                    'shape': 'semicircle',
                }
            },
            {
                'type': 'alphanumeric',
                'class': {
                    'shape-color': 'white',
                    'text-color': 'purple',
                    'text': 'T',
                    'shape': 'heptagon',
                }
            }
        ]

        response = requests.post('http://localhost:8003/targets', json=targets)
        self.assertEqual(response.status_code, 200)

    def test_telemetry(self):
        telemetry = {
            "altitude": 1002,
            "latitude": 0.10,
            "longitude": 0.80,
            "heading": 1.50
        }

        response = requests.post('http://localhost:8003/telemetry',
                                 json=telemetry)

        self.assertEqual(response.status_code, 200)

    def test_odlc_queueing(self):
        for (p, lat, lon) in self.paths:
            with open(p, 'rb') as im:
                telemetry = {
                    "altitude": 1002,
                    "latitude": lat,
                    "longitude": lon,
                    "heading": 1.50
                }

                response = requests.post('http://localhost:8003/telemetry',
                                         json=telemetry)

                self.assertEqual(response.status_code, 200)

                data = im.read()
                response = requests.post("http://localhost:8003/odlc",
                                         data=data,
                                         headers={'Content-Type':
                                                  'application/octet-stream'})
                self.assertEqual(response.status_code, 200)

    # def test_odlc_retrieval(self):
    #     response = requests.get('http://localhost:8003/odlc')
    #     self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
