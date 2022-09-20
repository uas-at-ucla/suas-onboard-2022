
"""
Stateful representation of vision subsystem
"""

import os
import math

from odlc import inference


def get_detection_confidence(detection):
    """
    Assign numerical value to the confidence we have in a detection
    Currently only considers the number of times it has been detected
    Potential ideas: location stdev
    """
    return detection['count']


def get_detection_diff(d_1, d_2):
    """
    Determine if two detections are different
    Currently considers detection type and whether the distance between
    coordinates is within our allowed tolerance
    """
    if d_1['type'] != d_2['type']:
        return float('inf')

    # Convert bounding boxes to vectors and calculate Euclidean distance
    b_1 = d_1['coords']
    b_2 = d_2['coords']
    dist = math.sqrt(((b_1[0]-b_2[0]) ** 2) + ((b_1[1]-b_2[1]) ** 2))

    return dist


class Detector:
    """Detector class: stateful methods"""
    def __init__(self):
        """
        Constructor for Detector class
        """
        self.detections = []
        self.num_detections = int(os.environ.get('NUM_DETECTIONS'))
        self.tolerance = int(os.environ.get('DETECTION_TOLERANCE'))
        self.expected_targets = []

    def update_targets(self, targets):
        self.num_detections = len(targets)
        self.expected_targets = targets

    def process_queued_image(self, img):
        """
        Main routine for image processing
        """
        print(img.shape)

        # Get emergent detections
        emergent_detections = inference.detect_mannikins(img)
        for detection in emergent_detections:
            # Find most similar existing detection
            min_diff = float('inf')
            min_comp = {}
            for comp in self.detections:
                diff = get_detection_diff(comp, detection)
                if diff < min_diff:
                    min_diff = diff
                    min_comp = comp

            # If they are similar enough, combine detections, otherwise
            # add the new detection to the detection list
            if min_diff < self.tolerance:
                print('Duplicate detected:')
                print(min_comp)
                print(detection)

                # What happens when duplicate detected
                # Update min_comp count, weighted average, stdev, etc.
            else:
                print('New detection found')
                print(detection)
                self.detections.append(detection)

    def get_top_detections(self):
        """
        Returns the top N detections we are most confident in
        """
        # If not enough detections, return everything we have so far
        if len(self.detections) <= self.num_detections:
            return self.detections

        # Sort detections increasing by confidence and return
        self.detections.sort(key=lambda x: -1.0 * get_detection_confidence(x))
        return self.detections[0:self.num_detections]
