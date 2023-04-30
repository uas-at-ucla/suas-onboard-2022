import traceback
import decorator
import time


def safe_function_call(func, default, retries, *args):
    tries = 0
    while tries < retries:
        try:
            return func(*args)
        except:
            traceback.print_exec()
            tries += 1
    return default


def retry(attempts):
    @decorator.decorator
    def do(func, *fargs, **fkwargs):
        for _ in range(attempts):
            try:
                return func(*fargs, **fkwargs)
            except Exception as e:
                traceback.print_stack(e)
                time.sleep(0.5)
        raise RetryException(f"Failed after retry {attempts} times")
    return do


class RetryException(Exception):
    def __init__(self, *args: object) -> None:
        super().__init__(*args)


if __name__ == "__main__":
    @retry(5)
    def test():
        print("TEST")

    test()