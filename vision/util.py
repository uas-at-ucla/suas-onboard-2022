import sys
import traceback
import os

import cv2

debugging = (int(os.environ.get('DEBUG')) == 1)


def info(message):
    print(f"[INFO] | {message}")
    sys.stdout.flush()


def error(message):
    print(f"[ERROR] | {message}")
    sys.stdout.flush()


def debug_info(message):
    if debugging:
        info(message)


def debug_imwrite(img, path):
    if debugging:
        cv2.imwrite(path, img)


def safe_function_call(func, default, *args):
    try:
        return func(*args),
    except Exception:  # pylint: disable=broad-except
        traceback.print_exc()
        return default
