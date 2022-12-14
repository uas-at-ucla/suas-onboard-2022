import os
import warnings
from functools import wraps

from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo

import numpy as np

import util as util


def ignore_warnings(f):
    @wraps(f)
    def inner(*args, **kwargs):

        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("ignore")
            response = f(*args, **kwargs)
        return response
    return inner


def iou(bb1, bb2):
    ix1 = np.maximum(bb1[0], bb2[0])
    iy1 = np.maximum(bb1[1], bb2[1])
    ix2 = np.maximum(bb1[2], bb2[2])
    iy2 = np.maximum(bb1[3], bb2[3])

    # Intersection height and width.
    i_height = np.maximum(iy2 - iy1 + 1, np.array(0.))
    i_width = np.maximum(ix2 - ix1 + 1, np.array(0.))

    area_of_intersection = i_height * i_width

    # Ground Truth dimensions.
    gt_height = bb1[3] - bb1[1] + 1
    gt_width = bb2[2] - bb1[0] + 1

    # Prediction dimensions.
    pd_height = bb2[3] - bb2[1] + 1
    pd_width = bb2[2] - bb2[0] + 1

    area_of_union = gt_height * gt_width + \
        pd_height * pd_width - area_of_intersection

    iou = area_of_intersection / area_of_union

    return iou


class Model:
    def __init__(self, model_path):
        util.info('Initializing model')
        cfg = get_cfg()
        cfg.MODEL.DEVICE = 'cpu'
        cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegment"
                                                      "ation/mask_rcnn_R_50_"
                                                      "FPN_3x.yaml"))
        cfg.MODEL.WEIGHTS = model_path
        cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        if 'alphanumeric_model' in model_path:
            cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = \
                float(os.environ.get('ALPHANUMERIC_MODEL_THRESHOLD'))
        else:
            cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = \
                float(os.environ.get('EMERGENT_MODEL_THRESHOLD'))

        self.predictor = DefaultPredictor(cfg)
        util.info('Model initialized')

    @ignore_warnings
    def detect_boxes(self, img):
        outputs = self.predictor(img)
        to = outputs['instances'].get_fields()['pred_boxes'].tensor

        # Convert tensor to list of lists
        out = []
        for i in range(to.shape[0]):
            out.append([to[i][j] for j in range(4)])

        # Remove duplicates (anything with >= 95% overlap)
        i = 0
        while i < len(out):
            ind = -1
            for j in range(i+1, len(out)):
                if iou(out[i], out[j]) >= 0.95:
                    ind = j
                    break

            if ind == -1:
                i += 1
            else:  # Duplicate detected, converge into single detection
                out[i] = [(out[i][k] + out[j][k]) / 2 for k in range(4)]
                out.pop(j)

        return out
