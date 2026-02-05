import unittest
import run

class TestEnterprise(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = run.app.test_client()

    def test_lexnet_plazos(self):
        r = self.client.post('/api/lexnet/analizar-plazo', json={'dias': 20})
        self.assertLess(r.status_code, 500)
        data = r.get_json()
        self.assertTrue(data.get('success'))
        self.assertIn('fecha_limite', data)

    def test_autoprocesar_status(self):
        r = self.client.get('/api/watchdog-status')
        self.assertLess(r.status_code, 500)
        self.assertIn('status', r.get_json())

if __name__ == '__main__':
    unittest.main()
