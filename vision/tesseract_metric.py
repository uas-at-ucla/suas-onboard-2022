from label_studio_sdk import Client
import requests
import numpy as np
import cv2
import json
from odlc import tesseract
from tqdm import tqdm
from sklearn.metrics import accuracy_score

LABEL_STUDIO_URL = "INSERT_URL"
API_KEY = "INSERT_API_KEY"


def percent_to_pixel(value, percentage_value):
    converted_value = int(value * percentage_value / 100)
    if converted_value >= value:
        return value
    if converted_value < 0:
        return 0
    return converted_value


def get_image_from_url(url_path):
    head = {"Authorization": "token {}".format(API_KEY)}
    response = requests.get(url_path, headers=head, stream=True).raw
    image = np.asarray(bytearray(response.read()), dtype="uint8")
    image = cv2.imdecode(image, cv2.IMREAD_COLOR)
    return image


def prediction_counts_as_correct(det, y_true):
    if len(det) == 0:
        return False
    # take the top three
    det = det[:3]
    chars = map(lambda pair: str(pair[0]), det)
    if y_true in chars:
        return True
    return False


if __name__ == "__main__":
    ls = Client(url=LABEL_STUDIO_URL, api_key=API_KEY)
    ls.check_connection()

    project = ls.get_projects()[0]

    labeled_tasks = project.get_labeled_tasks()

    y_true = []
    y_pred = []

    for task in tqdm(labeled_tasks):
        annotations = task["annotations"]
        for annotation in annotations:
            results = annotation["result"]
            is_shape = False
            for result in results:
                if "value" not in result.keys():
                    continue
                if "labels" not in result["value"].keys():
                    continue
                if "Emergent" in result["value"]["labels"]:
                    continue
                is_shape = True

            if not is_shape:
                continue

            annotation_value = {}
            img_height = -1
            img_width = -1

            for result in results:
                if "text" in result["value"]:
                    annotation_value = result["value"]
                    img_height = result["original_height"]
                    img_width = result["original_width"]
                    break

            if annotation_value == {}:
                continue

            # check if annotation has text value
            ocr_annotation_raw = annotation_value["text"][0]
            ocr_annotation_raw = ocr_annotation_raw.replace("\"", "")
            ocr_annotation_raw = ocr_annotation_raw.replace("\'", "\"")
            ocr_annotation_raw = "{" + ocr_annotation_raw + "}"
            try:
                ocr_annotation = json.loads(ocr_annotation_raw)
            except json.decoder.JSONDecodeError:
                continue
            if "text" not in ocr_annotation:
                continue
            if "x" not in annotation_value or "y" not in annotation_value:
                continue
            bbox_x = percent_to_pixel(img_width, annotation_value["x"])
            bbox_y = percent_to_pixel(img_height, annotation_value["y"])
            bbox_width = percent_to_pixel(img_width, annotation_value["width"])
            bbox_height = percent_to_pixel(
                img_height,
                annotation_value["height"]
            )

            url_path = "https://uas.seas.ucla.edu/" + task["data"]["ocr"]
            image = get_image_from_url(url_path)
            image = image[bbox_y: bbox_y+bbox_width, bbox_x: bbox_x+bbox_width]

            tesseract_det = tesseract.get_matching_text(image)
            task_y_true = ocr_annotation["text"]
            y_true.append(task_y_true)

            if prediction_counts_as_correct(tesseract_det, task_y_true):
                y_pred.append(task_y_true)
            else:
                y_pred.append("NONE")

    print(accuracy_score(y_true, y_pred))
