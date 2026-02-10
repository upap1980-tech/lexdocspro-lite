import unittest
from unittest.mock import patch

from services.ai_core_adapter_service import AICoreAdapterService


class DummyResponse:
    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


class TestAICoreAdapterService(unittest.TestCase):
    @patch('services.ai_core_adapter_service.requests.get')
    def test_health(self, mock_get):
        mock_get.return_value = DummyResponse({'status': 'ok'})
        svc = AICoreAdapterService(base_url='http://localhost:5011', sdk_path='/tmp/does-not-exist')
        data = svc.health()
        self.assertEqual(data.get('status'), 'ok')

    @patch('services.ai_core_adapter_service.requests.get')
    def test_health_ocr(self, mock_get):
        mock_get.return_value = DummyResponse({'available': True, 'engine': 'tesseract'})
        svc = AICoreAdapterService(base_url='http://localhost:5011', sdk_path='/tmp/does-not-exist')
        data = svc.health_ocr()
        self.assertTrue(data.get('available'))

    @patch('services.ai_core_adapter_service.requests.post')
    def test_chat(self, mock_post):
        mock_post.return_value = DummyResponse({'success': True, 'response': 'ok'})
        svc = AICoreAdapterService(base_url='http://localhost:5011', sdk_path='/tmp/does-not-exist')
        data = svc.chat(message='hola', project_id='LexDocsPro-LITE')
        self.assertTrue(data.get('success'))


if __name__ == '__main__':
    unittest.main()
