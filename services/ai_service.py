"""
Servicio Multi-IA para LexDocsPro
Soporta: Ollama, OpenAI, Perplexity, Gemini, DeepSeek, Groq
"""
import os
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()

class AIService:
    """Servicio unificado para múltiples proveedores de IA"""
    
    def __init__(self):
        self.providers = {
            'ollama': OllamaProvider(),
            'openai': OpenAIProvider(),
            'perplexity': PerplexityProvider(),
            'gemini': GeminiProvider(),
            'deepseek': DeepSeekProvider(),
            'groq': GroqProvider()  # NUEVO
        }
        self.default_provider = os.getenv('DEFAULT_AI_PROVIDER', 'ollama')
        
    def chat(self, prompt: str, context: str = '', provider: str = None, 
             mode: str = 'standard') -> Dict:
        """
        Chat con IA seleccionada
        
        Args:
            prompt: Pregunta del usuario
            context: Contexto del documento (opcional)
            provider: ollama, openai, perplexity, gemini, deepseek, groq
            mode: standard, deep, research
        """
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            return {'error': f'Proveedor {provider_name} no disponible'}
        
        provider_instance = self.providers[provider_name]
        
        # Construir prompt según el modo
        full_prompt = self._build_prompt(prompt, context, mode)
        
        try:
            response = provider_instance.generate(full_prompt, mode)
            return {
                'provider': provider_name,
                'mode': mode,
                'response': response,
                'success': True
            }
        except Exception as e:
            return {
                'provider': provider_name,
                'error': str(e),
                'success': False
            }
    
    def _build_prompt(self, prompt: str, context: str, mode: str) -> Dict:
        """Construir prompt según el modo de consulta"""
        
        base_system = """Eres un asistente legal especializado en derecho español.
Tu especialización incluye: Derecho Civil, Mercantil, Laboral, Administrativo y Procesal.
Cita siempre artículos específicos de leyes españolas cuando sea relevante."""
        
        if mode == 'deep':
            system = base_system + """

MODO DE ANÁLISIS PROFUNDO:
- Proporciona análisis exhaustivo con múltiples perspectivas
- Cita jurisprudencia relevante del Tribunal Supremo
- Analiza pros y contras de diferentes interpretaciones
- Identifica riesgos legales potenciales
- Proporciona fundamentación doctrinal cuando proceda
- Estructura: 1) Hechos, 2) Normativa, 3) Jurisprudencia, 4) Análisis, 5) Conclusiones"""
            
        elif mode == 'research':
            system = base_system + """

MODO DE INVESTIGACIÓN JURÍDICA:
- Busca y analiza normativa aplicable en profundidad
- Identifica todas las leyes, reglamentos y jurisprudencia relevante
- Compara interpretaciones doctrinales
- Analiza evolución legislativa si es relevante
- Proporciona referencias completas (BOE, sentencias, etc.)
- Identifica lagunas legales o áreas grises"""
            
        else:  # standard
            system = base_system
        
        user_prompt = prompt
        if context:
            user_prompt = f"""DOCUMENTO ANALIZADO:
{context[:4000]}

CONSULTA:
{prompt}"""
        
        return {
            'system': system,
            'user': user_prompt
        }
    
    def get_available_providers(self) -> List[str]:
        """Listar proveedores disponibles"""
        available = []
        for name, provider in self.providers.items():
            if provider.is_available():
                available.append(name)
        return available


class OllamaProvider:
    """Proveedor Ollama (local)"""
    
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'lexdocs-legal')
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        response = requests.post(
            f'{self.base_url}/api/generate',
            json={
                'model': self.model,
                'prompt': f"{prompt_dict['system']}\n\n{prompt_dict['user']}",
                'stream': False,
                'options': {
                    'temperature': 0.3 if mode == 'standard' else 0.5,
                    'num_ctx': 16384 if mode == 'deep' else 8192,
                    'num_predict': 4000 if mode == 'deep' else 2000
                }
            },
            timeout=120
        )
        return response.json().get('response', 'Sin respuesta')
    
    def is_available(self) -> bool:
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=2)
            return response.status_code == 200
        except:
            return False


class OpenAIProvider:
    """Proveedor OpenAI (ChatGPT)"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = 'gpt-4-turbo-preview'
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("OpenAI API key no configurada")
        
        from openai import OpenAI
        client = OpenAI(api_key=self.api_key)
        
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": prompt_dict['system']},
                {"role": "user", "content": prompt_dict['user']}
            ],
            temperature=0.3 if mode == 'standard' else 0.5,
            max_tokens=4000 if mode == 'deep' else 2000
        )
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class GroqProvider:
    """Proveedor Groq (ULTRA RÁPIDO)"""
    
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.model = 'llama-3.1-70b-versatile'  # Recomendado para análisis legal
        # Otros modelos disponibles:
        # - llama-3.1-8b-instant (más rápido, menos potente)
        # - mixtral-8x7b-32768 (muy bueno para español)
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("Groq API key no configurada. Obtén una gratis en: https://console.groq.com")
        
        from groq import Groq
        client = Groq(api_key=self.api_key)
        
        # Seleccionar modelo según modo
        if mode == 'deep' or mode == 'research':
            model = 'llama-3.1-70b-versatile'  # Más potente
        else:
            model = 'llama-3.1-8b-instant'  # Más rápido
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": prompt_dict['system']},
                {"role": "user", "content": prompt_dict['user']}
            ],
            temperature=0.3 if mode == 'standard' else 0.5,
            max_tokens=4000 if mode == 'deep' else 2000
        )
        return response.choices[0].message.content
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class PerplexityProvider:
    """Proveedor Perplexity"""
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.model = 'llama-3.1-sonar-large-128k-online'
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("Perplexity API key no configurada")
        
        response = requests.post(
            'https://api.perplexity.ai/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': self.model,
                'messages': [
                    {"role": "system", "content": prompt_dict['system']},
                    {"role": "user", "content": prompt_dict['user']}
                ],
                'temperature': 0.3 if mode == 'standard' else 0.5,
                'max_tokens': 4000 if mode == 'deep' else 2000
            },
            timeout=60
        )
        return response.json()['choices'][0]['message']['content']
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class GeminiProvider:
    """Proveedor Google Gemini"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.model = 'gemini-pro'
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("Gemini API key no configurada")
        
        import google.generativeai as genai
        genai.configure(api_key=self.api_key)
        model = genai.GenerativeModel(self.model)
        
        full_prompt = f"{prompt_dict['system']}\n\n{prompt_dict['user']}"
        response = model.generate_content(full_prompt)
        return response.text
    
    def is_available(self) -> bool:
        return bool(self.api_key)


class DeepSeekProvider:
    """Proveedor DeepSeek"""
    
    def __init__(self):
        self.api_key = os.getenv('DEEPSEEK_API_KEY')
        self.base_url = 'https://api.deepseek.com/v1'
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("DeepSeek API key no configurada")
        
        response = requests.post(
            f'{self.base_url}/chat/completions',
            headers={
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json'
            },
            json={
                'model': 'deepseek-chat',
                'messages': [
                    {"role": "system", "content": prompt_dict['system']},
                    {"role": "user", "content": prompt_dict['user']}
                ],
                'temperature': 0.3 if mode == 'standard' else 0.5
            },
            timeout=60
        )
        return response.json()['choices'][0]['message']['content']
    
    def is_available(self) -> bool:
        return bool(self.api_key)
