import unittest

from odlc import tesseract


class TesseractTests(unittest.TestCase):
    image_path_1 = '/app/images/test/tesseract-test1.png'
    image_path_2 = '/app/images/test/tesseract-test2.png'
    image_path_3 = '/app/images/test/tesseract-test3.png'
    image_path_4 = '/app/images/test/tesseract-test4.png'

    def test_tesseract_image_1(self):
        det = tesseract.get_matching_text(self.image_path_1)
        self.assertEqual(det[0][0], "A")

    def test_tesseract_image_2(self):
        det = tesseract.get_matching_text(self.image_path_2)
        self.assertEqual(det[0][0], "A")

    def test_tesseract_image_3(self):
        det = tesseract.get_matching_text(self.image_path_3)
        self.assertEqual(det[0][0], "A")

    def test_tesseract_image_4(self):
        det = tesseract.get_matching_text(self.image_path_4)
        self.assertEqual(det[0][0], "A")

if __name__ == "__main__":
    unittest.main()
