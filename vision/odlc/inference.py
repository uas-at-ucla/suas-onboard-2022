import os
import warnings
from functools import wraps

from detectron2.engine import DefaultPredictor
from detectron2.config import get_cfg
from detectron2 import model_zoo

import log


def ignore_warnings(f):
    @wraps(f)
    def inner(*args, **kwargs):

        with warnings.catch_warnings(record=True) as _:
            warnings.simplefilter("ignore")
            response = f(*args, **kwargs)
        return response
    return inner


class Model:
    def __init__(self, model_path):
        log.info('Initializing model')
        cfg = get_cfg()
        cfg.MODEL.DEVICE = 'cpu'
        cfg.merge_from_file(model_zoo.get_config_file("COCO-InstanceSegment"
                                                      "ation/mask_rcnn_R_50_"
                                                      "FPN_3x.yaml"))
        cfg.MODEL.WEIGHTS = model_path
        cfg.MODEL.ROI_HEADS.BATCH_SIZE_PER_IMAGE = 128
        cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = \
            float(os.environ.get('ALPHANUMERIC_MODEL_THRESHOLD'))

        self.predictor = DefaultPredictor(cfg)
        log.info('Model initialized')

    @ignore_warnings
    def detect_boxes(self, img):
        outputs = self.predictor(img)

        return outputs['instances'].get_fields()['pred_boxes'].tensor


def detect_mannikins(img):
    """TODO: mannikin detection model inference"""
    return []
