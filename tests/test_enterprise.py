import unittest
import requests

class TestEnterprise(unittest.TestCase):
    BASE_URL = 'http://localhost:5001'

    def test_lexnet_plazos(self):
        r = requests.post(f'{self.BASE_URL}/api/lexnet-analyze', json={'textos': {'test': 'demanda 04/02/2026'}})
        self.assertIn('20 días hábiles', r.json()['analisis'])

    def test_autoprocesar_status(self):
        r = requests.get(f'{self.BASE_URL}/api/watchdog-status')
        self.assertIn('status', r.json())

if __name__ == '__main__':
    unittest.main()
