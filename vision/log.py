import sys


def info(message):
    print(f"[INFO] | {message}")
    sys.stdout.flush()


def error(message):
    print(f"[ERROR] | {message}")
    sys.stdout.flush()
