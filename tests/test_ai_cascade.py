import sys
import os
import unittest
from unittest.mock import MagicMock, patch

# Añadir path para importar servicios
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ai_service import AIService

class TestAICascade(unittest.TestCase):
    def setUp(self):
        self.ai_service = AIService()
        # Mock de proveedores
        for p in self.ai_service.providers:
            self.ai_service.providers[p].is_available = MagicMock(return_value=True)
            self.ai_service.providers[p].generate = MagicMock()

    def test_cascade_success_first_try(self):
        """Ollama funciona a la primera"""
        self.ai_service.providers['ollama'].generate.return_value = "Respuesta Ollama"
        
        result = self.ai_service.chat_cascade("Hola", providers=['ollama', 'groq'])
        
        self.assertTrue(result['success'])
        self.assertEqual(result['provider'], 'ollama')
        self.assertEqual(result['response'], 'Respuesta Ollama')
        self.ai_service.providers['groq'].generate.assert_not_called()

    def test_cascade_fallback_to_second(self):
        """Ollama falla, salta a Groq"""
        self.ai_service.providers['ollama'].generate.side_effect = Exception("Ollama offline")
        self.ai_service.providers['groq'].generate.return_value = "Respuesta Groq"
        
        result = self.ai_service.chat_cascade("Hola", providers=['ollama', 'groq'])
        
        self.assertTrue(result['success'])
        self.assertEqual(result['provider'], 'groq')
        self.assertEqual(result['response'], 'Respuesta Groq')

    def test_cascade_total_failure(self):
        """Todos los proveedores fallan"""
        for p in self.ai_service.providers:
            self.ai_service.providers[p].generate.side_effect = Exception("Error total")
            
        result = self.ai_service.chat_cascade("Hola", providers=['ollama', 'groq'])
        
        self.assertFalse(result['success'])
        self.assertIn("Cascada agotada", result['error'])

if __name__ == '__main__':
    unittest.main()
