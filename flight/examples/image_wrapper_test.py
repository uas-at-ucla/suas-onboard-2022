# Test script for image wrapper
import unittest
import threading
from unittest.mock import patch
from image_wrapper import (index, get_best_object_detections,
                           queue_image_for_odlc, update_telemetry,
                           update_targets, get_status)


class TestImageWrapper(unittest.TestCase):

    @patch('requests.get')
    def test_index(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'key': 'value'}
        result = index()
        self.assertEqual(result, {'key': 'value'})

    @patch('requests.get')
    def test_get_best_object_detections(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'key': 'value'}
        result = get_best_object_detections()
        self.assertEqual(result, {'key': 'value'})

    @patch('requests.post')
    def test_queue_image_for_odlc(self, mock_post):
        mock_post.return_value.status_code = 200
        stop_event = threading.Event()
        thread = threading.Thread(target=queue_image_for_odlc,
                                  args=('image_png', stop_event))
        thread.start()
        stop_event.wait(timeout=2.5)
        stop_event.set()
        thread.join(timeout=0.1)
        self.assertGreaterEqual(mock_post.call_count, 9)
        print("Test successful")

    @patch('requests.post')
    def test_update_telemetry(self, mock_post):
        mock_post.return_value.status_code = 200
        update_telemetry(1, 2, 3, 4)
        mock_post.assert_called_once_with(
            'http://localhost:8003/telemetry',
            json={'altitude': 1, 'latitude': 2, 'longitude': 3, 'heading': 4})

    @patch('requests.post')
    def test_update_targets(self, mock_post):
        mock_post.return_value.status_code = 200
        update_targets('type', 'shape_color', 'text_color', 'text', 'shape')
        mock_post.assert_called_once_with(
            'http://localhost:8003/targets',
            json={'type': 'type', 'class': {'shape-color': 'shape_color',
                                            'text-color': 'text_color',
                                            'text': 'text', 'shape': 'shape'}})

    @patch('requests.get')
    def test_get_status(self, mock_get):
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = {'key': 'value'}
        result = get_status()
        self.assertEqual(result, {'key': 'value'})


if __name__ == '__main__':
    unittest.main()
