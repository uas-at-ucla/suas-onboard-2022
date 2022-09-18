import odlc.inference as inference
import odlc.tesseract as tesseract
from model.types import Detections
import cv2
import os
import numpy as np

'''

Main detector class 

'''

class Detector:
    def __init__(self):
        self.detections = {}
        self.num_detections = os.environ.get('NUM_DETECTIONS')
        self.tolerance = os.environ.get('DETECTION_TOLERANCE')
    
    # Main routine for processing the image
    def process_queued_image(self, img):
        print(img.shape)
    
    # Returns the top N detections we are most confident in 
    def get_top_detections(self):
        return []