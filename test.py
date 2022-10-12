
import sys

from odlc import tesseract

success = []
failure = []


def check_result(res, anticipated, name):
    if res == anticipated:
        print(f'Test succeeded: {name}')
        success.append(name)
    else:
        failure.append(name)
        print(f'Test failed : {name}, expected {anticipated}, got {res}')


def test_tesseract():
    print('Testing Tesseract OCR integration...')
    det = tesseract.get_matching_text('/app/images/test/tesseract-test1.png')
    print(det)
    check_result(det[0][0], 'A', 'Tesseract1')
    det = tesseract.get_matching_text('/app/images/test/tesseract-test2.png')
    check_result(det[0][0], 'A', 'Tesseract2')
    print('Completed Tesseract OCR test')


def main():
    test_tesseract()
    num_tests = len(success) + len(failure)
    print('============================================')
    print(f'Passed {len(success)} of {num_tests} tests')
    print(f'Successful tests: {success}')
    print(f'Failed tests: {failure}')
    if len(failure) == 0:
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
