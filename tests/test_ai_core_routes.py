import io
import unittest
from unittest.mock import patch

import run


class TestAICoreRoutes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = run.app
        cls.client = cls.app.test_client()

    @patch.object(run.ai_core_adapter, 'health', return_value={'status': 'ok'})
    def test_ai_core_health(self, _mock_health):
        res = self.client.get('/api/ai-core/health')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))
        self.assertEqual(body['data']['status'], 'ok')

    @patch.object(run.ai_core_adapter, 'health_ocr', return_value={'available': True, 'engine': 'tesseract'})
    def test_ai_core_health_ocr(self, _mock_ocr):
        res = self.client.get('/api/ai-core/health/ocr')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))
        self.assertTrue(body['data']['available'])

    @patch.object(run.ai_core_adapter, 'chat', return_value={'success': True, 'response': 'ok'})
    def test_ai_core_chat(self, _mock_chat):
        res = self.client.post('/api/ai-core/chat', json={'message': 'hola', 'project_id': 'LexDocsPro-LITE'})
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))

    @patch.object(run.ai_core_adapter, 'rag_upload', return_value={'success': True})
    def test_ai_core_rag_upload_json(self, _mock_upload):
        res = self.client.post(
            '/api/ai-core/rag/upload',
            json={'project_id': 'LexDocsPro-LITE', 'document_id': 'doc-1', 'content': 'texto legal'}
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))

    @patch.object(run.ai_core_adapter, 'rag_upload', return_value={'success': True})
    def test_ai_core_rag_upload_file(self, mock_upload):
        data = {
            'project_id': 'LexDocsPro-LITE',
            'document_id': 'doc-file',
            'file': (io.BytesIO(b'texto legal file'), 'sample.txt'),
        }
        res = self.client.post('/api/ai-core/rag/upload', data=data, content_type='multipart/form-data')
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))
        self.assertTrue(mock_upload.called)

    @patch.object(run.ai_core_adapter, 'delete_document', return_value={'success': True, 'removed_chunks': 2})
    def test_ai_core_rag_delete(self, _mock_delete):
        res = self.client.post(
            '/api/ai-core/rag/delete',
            json={'project_id': 'LexDocsPro-LITE', 'document_id': 'doc-1'}
        )
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))

    @patch.object(run.ai_core_adapter, 'reindex', return_value={'success': True, 'indexed_chunks': 10})
    def test_ai_core_rag_reindex(self, _mock_reindex):
        res = self.client.post('/api/ai-core/rag/reindex', json={})
        self.assertEqual(res.status_code, 200)
        body = res.get_json()
        self.assertTrue(body.get('success'))


if __name__ == '__main__':
    unittest.main()
