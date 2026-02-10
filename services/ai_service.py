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

    # ---------- Gestión de modelos Ollama ----------
    def get_ollama_models(self) -> Dict:
        provider = self.providers.get('ollama')
        if not provider:
            return {'success': False, 'error': 'Proveedor Ollama no disponible'}
        return provider.list_models()

    def set_ollama_model(self, model_name: str) -> Dict:
        provider = self.providers.get('ollama')
        if not provider:
            return {'success': False, 'error': 'Proveedor Ollama no disponible'}
        return provider.set_model(model_name)
        
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

            
    def stream_chat(self, prompt: str, context: str = '', provider: str = None, mode: str = 'standard'):
        """Generador para streaming"""
        provider_name = provider or self.default_provider
        
        if provider_name not in self.providers:
            yield f"Error: Proveedor {provider_name} no disponible"
            return
            
        provider_instance = self.providers[provider_name]
        full_prompt = self._build_prompt(prompt, context, mode)
        
        # Intentar usar RAG Skill si estamos en modo research
        if mode == 'research' and hasattr(self, 'rag_skill'):
             rag_context = self.rag_skill.retrieve_context(prompt)
             if rag_context:
                 full_prompt['user'] += f"\n\nCONTEXTO RAG ADICIONAL:\n{rag_context}"
        
        try:
            # Check if provider supports streaming
            if hasattr(provider_instance, 'generate_stream'):
                for chunk in provider_instance.generate_stream(full_prompt, mode):
                    yield chunk
            else:
                # Fallback to sync
                response = provider_instance.generate(full_prompt, mode)
                yield response
        except Exception as e:
            yield f"Error: {str(e)}"
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
    
    def consultar(self, texto: str, pregunta: str, provider: str = None, mode: str = 'standard', max_length: int = None) -> str:
        """
        Método de consulta rápida sobre un texto
        Compatible con llamadas desde el frontend
        
        Args:
            texto: Contenido del documento/texto a analizar
            pregunta: Pregunta o instrucción del usuario
            provider: Proveedor de IA a usar (opcional)
            mode: Modo de análisis ('standard', 'deep', 'research')
            max_length: Longitud máxima del texto (opcional, no usado actualmente)
            
        Returns:
            str: Respuesta de la IA
        """
        # Si el texto es muy largo, truncar manteniendo inicio y fin
        if max_length and len(texto) > max_length:
            mid = max_length // 2
            texto = texto[:mid] + "\n\n[...contenido omitido...]\n\n" + texto[-mid:]
        
        result = self.chat(
            prompt=pregunta,
            context=texto,
            provider=provider,
            mode=mode
        )
        
        if result.get('success'):
            return result.get('response', 'Sin respuesta')
        else:
            error_msg = result.get('error', 'Desconocido')
            return f"Error al consultar IA: {error_msg}"

class OllamaProvider:
    """Proveedor Ollama (local)"""
    
    def __init__(self):
        self.base_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.model = os.getenv('OLLAMA_MODEL', 'lexdocs-legal')
        self._cached_models = None

    def list_models(self) -> Dict:
        try:
            resp = requests.get(f"{self.base_url}/api/tags", timeout=3)
            data = resp.json()
            models = [m.get('name') for m in data.get('models', []) if m.get('name')]
            self._cached_models = models
            return {
                'success': True,
                'models': models,
                'current': self.model
            }
        except Exception as e:
            return {
                'success': False,
                'error': f"No se pudieron listar modelos Ollama: {e}",
                'current': self.model,
                'models': self._cached_models or []
            }

    def set_model(self, model_name: str) -> Dict:
        if not model_name:
            return {'success': False, 'error': 'Nombre de modelo vacío'}
        # Validar contra lista si está disponible; si falla, aún permite setear.
        models_info = self.list_models()
        if models_info.get('success') and models_info.get('models'):
            if model_name not in models_info['models']:
                return {'success': False, 'error': f"Modelo '{model_name}' no está disponible en Ollama"}
        self.model = model_name
        return {'success': True, 'current': self.model}
    
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

    def generate_stream(self, prompt_dict: Dict, mode: str):
        # Ollama Streaming
        try:
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': f"{prompt_dict['system']}\n\n{prompt_dict['user']}",
                    'stream': True,
                    'options': {
                        'temperature': 0.3 if mode == 'standard' else 0.5
                    }
                },
                stream=True,
                timeout=120
            )
            
            for line in response.iter_lines():
                if line:
                    import json
                    try:
                        json_resp = json.loads(line)
                        if 'response' in json_resp:
                            yield json_resp['response']
                    except:
                        pass
        except Exception as e:
            yield f"Error streaming: {str(e)}"


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
        self.model = 'llama-3.1-70b-versatile'
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("Groq API key no configurada. Obtén una gratis en: https://console.groq.com")
        
        try:
            from groq import Groq
            
            # Inicializar cliente SIN parámetros opcionales problemáticos
            client = Groq(api_key=self.api_key)
            
            # Seleccionar modelo según modo
            if mode == 'deep' or mode == 'research':
                model = 'llama-3.1-70b-versatile'
            else:
                model = 'llama-3.1-8b-instant'
            
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
            
        except ImportError:
            raise Exception("Librería 'groq' no instalada. Instala con: pip install groq")
        except Exception as e:
            raise Exception(f"Error en Groq: {str(e)}")
    
    def is_available(self) -> bool:
        if not self.api_key:
            return False
        try:
            from groq import Groq
            return True
        except ImportError:
            return False

class PerplexityProvider:
    """Proveedor Perplexity PRO con soporte multimodal"""
    
    def __init__(self):
        self.api_key = os.getenv('PERPLEXITY_API_KEY')
        self.model = os.getenv('PERPLEXITY_MODEL', 'llama-3.1-sonar-large-128k-online')
        self.base_url = 'https://api.perplexity.ai/chat/completions'
    
    def generate(self, prompt_dict: Dict, mode: str) -> str:
        if not self.api_key:
            raise Exception("Perplexity API key no configurada")
        
        try:
            # Construir mensajes según el formato de Perplexity
            messages = [
                {
                    "role": "system",
                    "content": prompt_dict.get('system', 'Eres un asistente legal especializado en derecho español.')
                },
                {
                    "role": "user",
                    "content": prompt_dict.get('user', prompt_dict.get('prompt', ''))
                }
            ]
            
            # Payload corregido para Perplexity API
            payload = {
                "model": self.model,
                "messages": messages,
                "temperature": 0.2 if mode == 'standard' else 0.4,
                "top_p": 0.9,
                "return_citations": True,  # Aprovechar capacidad de citas
                "return_images": False,     # Desactivar imágenes por ahora
                "search_recency_filter": "month",  # Búsqueda web reciente
                "top_k": 0,
                "stream": False,
                "presence_penalty": 0,
                "frequency_penalty": 1
            }
            
            headers = {
                'Authorization': f'Bearer {self.api_key}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            # Debug detallado
            print(f"[DEBUG] Perplexity Request:")
            print(f"  Model: {self.model}")
            print(f"  Messages: {len(messages)} mensajes")
            print(f"  User prompt: {messages[1]['content'][:100]}...")
            
            response = requests.post(
                self.base_url,
                headers=headers,
                json=payload,
                timeout=60  # Perplexity puede tardar más por búsqueda web
            )
            
            # Debug respuesta
            print(f"[DEBUG] Perplexity Response:")
            print(f"  Status: {response.status_code}")
            print(f"  Headers: {dict(response.headers)}")
            
            # Manejo de errores HTTP
            if response.status_code != 200:
                error_detail = response.text[:500]
                print(f"[ERROR] Perplexity: {error_detail}")
                
                if response.status_code == 400:
                    raise Exception(f"Formato incorrecto. Detalles: {error_detail}")
                elif response.status_code == 401:
                    raise Exception("API Key inválida o expirada")
                elif response.status_code == 429:
                    raise Exception("Límite de rate excedido. Espera 60 segundos.")
                elif response.status_code == 500:
                    raise Exception("Error interno de Perplexity. Intenta en unos minutos.")
                else:
                    raise Exception(f"Error HTTP {response.status_code}: {error_detail}")
            
            response.raise_for_status()
            data = response.json()
            
            # Debug estructura de respuesta
            print(f"[DEBUG] Response keys: {list(data.keys())}")
            
            # Extraer respuesta
            if 'choices' in data and len(data['choices']) > 0:
                content = data['choices'][0]['message']['content']
                
                # Agregar citas si están disponibles
                if 'citations' in data and data['citations']:
                    content += "\n\n📚 Fuentes consultadas:\n"
                    for i, citation in enumerate(data['citations'][:3], 1):
                        content += f"{i}. {citation}\n"
                
                return content
            else:
                raise Exception(f"Estructura de respuesta inesperada: {list(data.keys())}")
                
        except requests.exceptions.Timeout:
            raise Exception("Timeout - Perplexity tardó más de 60s. Intenta con un prompt más corto.")
        except requests.exceptions.ConnectionError:
            raise Exception("Error de conexión. Verifica tu internet.")
        except requests.exceptions.RequestException as e:
            raise Exception(f"Error de red: {str(e)}")
        except Exception as e:
            raise Exception(f"Error Perplexity: {str(e)}")
    
    def is_available(self) -> bool:
        """Verificar si Perplexity está disponible"""
        return bool(self.api_key and self.api_key.startswith('pplx-'))



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
