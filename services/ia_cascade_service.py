#!/usr/bin/env python3
"""
IA CASCADE SERVICE v3.0
Multi-provider con fallback automático y stats en tiempo real

PROVIDERS SOPORTADOS:
1. Ollama (local) - Privacidad máxima
2. Groq (cloud) - Rápido y gratuito
3. Perplexity (cloud) - Búsqueda aumentada
4. OpenAI (cloud) - GPT-4
5. Gemini (cloud) - Google
6. DeepSeek (cloud) - Alternativa china
7. Claude (cloud) - Anthropic

REGLA DE ORO: NUNCA perder capacidad de análisis por fallos de un provider
"""

import os
import time
import json
import threading
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from dotenv import load_dotenv

load_dotenv()


class IACascadeService:
    def __init__(self):
        ollama_url = self._resolve_ollama_url()
        claude_api_key = self._get_env(["CLAUDE_API_KEY", "ANTHROPIC_API_KEY"])
        # ============ CONFIGURACIÓN DE PROVIDERS ============
        self.providers_config = {
            'ollama': {
                'name': 'Ollama (Local)',
                'url': ollama_url,
                'model': os.getenv('OLLAMA_MODEL', 'llama3'),
                'enabled': True,
                'local': True,
                'priority': 1,
                'timeout': 120,
                'api_key': None  # No requiere
            },
            'groq': {
                'name': 'Groq Cloud',
                'url': 'https://api.groq.com/openai/v1/chat/completions',
                'model': os.getenv('GROQ_MODEL', 'llama-3.1-8b-instant'),
                'enabled': bool(os.getenv('GROQ_API_KEY')),
                'local': False,
                'priority': 2,
                'timeout': 30,
                'api_key': os.getenv('GROQ_API_KEY')
            },
            'perplexity': {
                'name': 'Perplexity AI',
                'url': 'https://api.perplexity.ai/chat/completions',
                'model': os.getenv('PERPLEXITY_MODEL', 'sonar-medium-online'),
                'enabled': bool(os.getenv('PERPLEXITY_API_KEY')),
                'local': False,
                'priority': 3,
                'timeout': 40,
                'api_key': os.getenv('PERPLEXITY_API_KEY')
            },
            'openai': {
                'name': 'OpenAI GPT-4',
                'url': 'https://api.openai.com/v1/chat/completions',
                'model': os.getenv('OPENAI_MODEL', 'gpt-4o-mini'),
                'enabled': bool(os.getenv('OPENAI_API_KEY')),
                'local': False,
                'priority': 4,
                'timeout': 60,
                'api_key': os.getenv('OPENAI_API_KEY')
            },
            'gemini': {
                'name': 'Google Gemini',
                'url': 'https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent',
                'model': os.getenv('GEMINI_MODEL', 'gemini-1.5-flash'),
                'enabled': bool(os.getenv('GEMINI_API_KEY')),
                'local': False,
                'priority': 5,
                'timeout': 50,
                'api_key': os.getenv('GEMINI_API_KEY')
            },
            'deepseek': {
                'name': 'DeepSeek',
                'url': 'https://api.deepseek.com/v1/chat/completions',
                'model': os.getenv('DEEPSEEK_MODEL', 'deepseek-chat'),
                'enabled': bool(os.getenv('DEEPSEEK_API_KEY')),
                'local': False,
                'priority': 6,
                'timeout': 40,
                'api_key': os.getenv('DEEPSEEK_API_KEY')
            },
            'claude': {
                'name': 'Anthropic Claude',
                'url': 'https://api.anthropic.com/v1/messages',
                'model': os.getenv('CLAUDE_MODEL', 'claude-3-opus-20240229'),
                'enabled': bool(claude_api_key),
                'local': False,
                'priority': 7,
                'timeout': 60,
                'api_key': claude_api_key
            }
        }
        # Añadir dinámicamente todos los modelos locales de Ollama como providers separados
        self._add_local_ollama_models(ollama_url)
        self.stats_lock = threading.Lock()
        
        # ============ ESTADÍSTICAS EN TIEMPO REAL ============
        self._init_stats()
        
        # Cargar stats persistentes si existen
        self._load_stats()
        
        # Provider por defecto
        self.default_provider = os.getenv('DEFAULT_AI_PROVIDER', 'ollama')
        
        print("=" * 70)
        print("🤖 IA CASCADE SERVICE v3.0 INICIALIZADO")
        print("=" * 70)
        self._print_providers_status()

    def _get_env(self, keys: List[str], default: Optional[str] = None) -> Optional[str]:
        for key in keys:
            value = os.getenv(key)
            if value:
                return value
        return default

    def _resolve_ollama_url(self) -> str:
        raw = self._get_env(["OLLAMA_URL", "OLLAMA_BASE_URL"], "http://localhost:11434")
        if not raw:
            return "http://localhost:11434/api/generate"
        raw = raw.rstrip("/")
        if raw.endswith("/api/generate"):
            return raw
        return f"{raw}/api/generate"

    def _add_local_ollama_models(self, ollama_url: str) -> None:
        """Descubre modelos locales de Ollama y los añade como providers adicionales."""
        try:
            base = ollama_url.replace("/api/generate", "")
            resp = requests.get(f"{base}/api/tags", timeout=2)
            data = resp.json()
            models = [m.get("name") for m in data.get("models", []) if m.get("name")]
        except Exception:
            models = []
        base_priority = 1
        for idx, model_name in enumerate(models, start=1):
            provider_id = f"ollama::{model_name}"
            if provider_id in self.providers_config:
                continue
            self.providers_config[provider_id] = {
                "name": f"Ollama Local ({model_name})",
                "url": ollama_url,
                "model": model_name,
                "enabled": True,
                "local": True,
                "priority": base_priority + idx,
                "timeout": 120,
                "api_key": None,
            }

    def _init_stats(self) -> None:
        self.stats = {
            provider: {
                "total_calls": 0,
                "successful_calls": 0,
                "failed_calls": 0,
                "total_time": 0.0,
                "avg_time": 0.0,
                "last_call": None,
                "last_error": None,
                "tokens_used": 0,
                "uptime_percentage": 100.0,
            }
            for provider in self.providers_config.keys()
        }

    def _sanitize_request(self, prompt: str, temperature: float, max_tokens: int) -> Tuple[str, float, int]:
        safe_prompt = (prompt or "").strip()
        safe_temp = max(0.0, min(1.0, float(temperature)))
        safe_tokens = int(max(32, min(8192, int(max_tokens or 0))))
        return safe_prompt, safe_temp, safe_tokens

    def _extract_tokens_from_metadata(self, metadata: Dict) -> int:
        if not metadata:
            return 0
        for key in ("tokens", "total_tokens", "completion_tokens", "output_tokens"):
            val = metadata.get(key)
            if isinstance(val, int):
                return max(0, val)
        return 0
    
    def _print_providers_status(self):
        """Imprimir estado de todos los providers"""
        print(f"\n📊 PROVIDERS CONFIGURADOS:")
        for provider_id, config in self.providers_config.items():
            status = "✅ ENABLED" if config['enabled'] else "❌ DISABLED"
            location = "🏠 Local" if config['local'] else "☁️  Cloud"
            print(f"  {config['priority']}. {config['name']:20} {status:12} {location:10} | Model: {config['model']}")
        print(f"\n🎯 Provider por defecto: {self.default_provider.upper()}")
        print("=" * 70 + "\n")
    
    # ============ CONSULTA CON CASCADE AUTOMÁTICO ============
    
    def consultar_cascade(
        self,
        prompt: str,
        temperature: float = 0.3,
        max_tokens: int = 2000,
        force_provider: Optional[str] = None
    ) -> Dict:
        """
        Consulta con cascade automático entre providers
        
        Args:
            prompt: Texto del prompt
            temperature: Creatividad (0.0-1.0)
            max_tokens: Tokens máximos de respuesta
            force_provider: Forzar un provider específico
        
        Returns:
            Dict con 'success', 'response', 'provider_used', 'time', 'metadata'
        """
        print(f"\n{'='*70}")
        print(f"🔍 CONSULTA IA CASCADE")
        print(f"{'='*70}")
        prompt, temperature, max_tokens = self._sanitize_request(prompt, temperature, max_tokens)
        if not prompt:
            return {
                'success': False,
                'error': 'Prompt vacío',
                'provider_used': None,
                'time': 0,
                'metadata': {'attempts': 0}
            }

        print(f"📝 Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
        print(f"🎛️  Temperature: {temperature} | Max Tokens: {max_tokens}")
        
        if force_provider:
            print(f"🎯 Provider forzado: {force_provider.upper()}")
            return self._call_provider(force_provider, prompt, temperature, max_tokens)
        
        # Ordenar providers por prioridad
        sorted_providers = sorted(
            [(k, v) for k, v in self.providers_config.items() if v['enabled']],
            key=lambda x: x[1]['priority']
        )
        if not sorted_providers:
            return {
                'success': False,
                'error': 'No hay providers habilitados',
                'provider_used': None,
                'time': 0,
                'metadata': {'attempts': 0}
            }
        
        print(f"\n🔄 Orden de fallback ({len(sorted_providers)} providers):")
        for i, (provider_id, config) in enumerate(sorted_providers, 1):
            print(f"  {i}. {config['name']}")
        
        # Intentar con cada provider en orden
        for provider_id, config in sorted_providers:
            print(f"\n{'─'*70}")
            print(f"🚀 Intentando con {config['name']}...")
            print(f"{'─'*70}")
            
            result = self._call_provider(provider_id, prompt, temperature, max_tokens)
            
            if result.get('success'):
                print(f"✅ ÉXITO con {config['name']}")
                print(f"⏱️  Tiempo: {result.get('time', 0):.2f}s")
                print(f"📊 Tokens: {result.get('metadata', {}).get('tokens', 'N/A')}")
                print(f"{'='*70}\n")
                return result
            else:
                print(f"❌ FALLÓ {config['name']}: {result.get('error', 'Unknown')}")
                print(f"🔄 Intentando siguiente provider...")
        
        # Todos los providers fallaron
        print(f"\n{'='*70}")
        print(f"❌ TODOS LOS PROVIDERS FALLARON")
        print(f"{'='*70}\n")
        return {
            'success': False,
            'error': 'Todos los providers de IA fallaron',
            'provider_used': None,
            'time': 0,
            'metadata': {'attempts': len(sorted_providers)}
        }
    
    # ============ LLAMADAS A PROVIDERS INDIVIDUALES ============
    
    def _call_provider(
        self,
        provider_id: str,
        prompt: str,
        temperature: float,
        max_tokens: int
    ) -> Dict:
        """Llamada a un provider específico con manejo de errores"""
        start_time = time.time()
        
        # Soporte para providers dinámicos ollama::<model>
        effective_provider = provider_id
        override_model = None
        if provider_id.startswith("ollama::"):
            effective_provider = "ollama"
            override_model = provider_id.split("::", 1)[1]

        if effective_provider not in self.providers_config:
            return {'success': False, 'error': f'Provider {provider_id} no existe'}
        
        config = self.providers_config[effective_provider].copy()
        if override_model:
            config['model'] = override_model
        
        if not config['enabled']:
            return {'success': False, 'error': f'Provider {provider_id} está deshabilitado'}
        
        # Actualizar stats
        with self.stats_lock:
            if provider_id not in self.stats:
                self._init_stats()
            self.stats[provider_id]['total_calls'] += 1
            self.stats[provider_id]['last_call'] = datetime.now().isoformat()
        
        try:
            # Llamar al método específico del provider
            if effective_provider == 'ollama':
                result = self._call_ollama(prompt, temperature, max_tokens, config)
            elif effective_provider == 'groq':
                result = self._call_groq(prompt, temperature, max_tokens, config)
            elif effective_provider == 'perplexity':
                result = self._call_perplexity(prompt, temperature, max_tokens, config)
            elif effective_provider == 'openai':
                result = self._call_openai(prompt, temperature, max_tokens, config)
            elif effective_provider == 'gemini':
                result = self._call_gemini(prompt, temperature, max_tokens, config)
            elif effective_provider == 'deepseek':
                result = self._call_deepseek(prompt, temperature, max_tokens, config)
            elif effective_provider == 'claude':
                result = self._call_claude(prompt, temperature, max_tokens, config)
            else:
                return {'success': False, 'error': f'Provider {provider_id} no implementado'}
            
            elapsed_time = time.time() - start_time
            
            if result.get('success'):
                # Actualizar stats de éxito
                with self.stats_lock:
                    self.stats[provider_id]['successful_calls'] += 1
                    self.stats[provider_id]['total_time'] += elapsed_time
                    self.stats[provider_id]['avg_time'] = (
                        self.stats[provider_id]['total_time'] /
                        self.stats[provider_id]['successful_calls']
                    )
                    tokens = self._extract_tokens_from_metadata(result.get('metadata', {}))
                    self.stats[provider_id]['tokens_used'] += tokens
                    total = self.stats[provider_id]['total_calls']
                    successful = self.stats[provider_id]['successful_calls']
                    self.stats[provider_id]['uptime_percentage'] = (successful / total) * 100 if total > 0 else 0
                
                result['time'] = elapsed_time
                result['provider_used'] = provider_id
                
                self._save_stats()
                return result
            else:
                raise Exception(result.get('error', 'Unknown error'))
        
        except Exception as e:
            elapsed_time = time.time() - start_time
            error_msg = str(e)
            
            # Actualizar stats de error
            with self.stats_lock:
                self.stats[provider_id]['failed_calls'] += 1
                self.stats[provider_id]['last_error'] = error_msg
                total = self.stats[provider_id]['total_calls']
                successful = self.stats[provider_id]['successful_calls']
                self.stats[provider_id]['uptime_percentage'] = (successful / total) * 100 if total > 0 else 0
            
            self._save_stats()
            
            return {
                'success': False,
                'error': error_msg,
                'provider_used': provider_id,
                'time': elapsed_time,
                'metadata': {}
            }
    
    # ============ IMPLEMENTACIONES POR PROVIDER ============
    
    def _call_ollama(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a Ollama local"""
        try:
            payload = {
                'model': config['model'],
                'prompt': prompt,
                'stream': False,
                'options': {
                    'temperature': temperature,
                    'num_predict': max_tokens,
                    'top_p': 0.9
                }
            }
            
            response = requests.post(
                config['url'],
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    'success': True,
                    'response': data.get('response', '').strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': len(data.get('response', '').split()),
                        'context': data.get('context', [])
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except requests.exceptions.Timeout:
            return {'success': False, 'error': f'Timeout después de {config["timeout"]}s'}
        except requests.exceptions.ConnectionError:
            return {'success': False, 'error': 'No se pudo conectar con Ollama (¿está ejecutándose?)'}
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_groq(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a Groq Cloud"""
        try:
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': config['model'],
                'messages': [
                    {'role': 'system', 'content': 'Eres un experto en derecho español.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': temperature,
                'max_tokens': max_tokens,
                'top_p': 0.9
            }
            
            response = requests.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'response': message.strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': data.get('usage', {}).get('total_tokens', 0),
                        'prompt_tokens': data.get('usage', {}).get('prompt_tokens', 0),
                        'completion_tokens': data.get('usage', {}).get('completion_tokens', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_perplexity(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a Perplexity AI"""
        try:
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': config['model'],
                'messages': [
                    {'role': 'system', 'content': 'Eres un experto en derecho español.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            response = requests.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'response': message.strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': data.get('usage', {}).get('total_tokens', 0),
                        'citations': data.get('citations', [])
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_openai(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a OpenAI GPT-4"""
        try:
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': config['model'],
                'messages': [
                    {'role': 'system', 'content': 'Eres un experto en derecho español.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            response = requests.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'response': message.strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': data.get('usage', {}).get('total_tokens', 0),
                        'prompt_tokens': data.get('usage', {}).get('prompt_tokens', 0),
                        'completion_tokens': data.get('usage', {}).get('completion_tokens', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_gemini(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a Google Gemini"""
        try:
            url = f"{config['url']}?key={config['api_key']}"
            
            payload = {
                'contents': [{
                    'parts': [{'text': prompt}]
                }],
                'generationConfig': {
                    'temperature': temperature,
                    'maxOutputTokens': max_tokens
                }
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['candidates'][0]['content']['parts'][0]['text']
                
                return {
                    'success': True,
                    'response': message.strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': data.get('usageMetadata', {}).get('totalTokenCount', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_deepseek(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a DeepSeek"""
        try:
            headers = {
                'Authorization': f'Bearer {config["api_key"]}',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': config['model'],
                'messages': [
                    {'role': 'system', 'content': 'Eres un experto en derecho español.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            response = requests.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['choices'][0]['message']['content']
                
                return {
                    'success': True,
                    'response': message.strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': data.get('usage', {}).get('total_tokens', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def _call_claude(self, prompt: str, temperature: float, max_tokens: int, config: Dict) -> Dict:
        """Llamada a Anthropic Claude"""
        try:
            headers = {
                'x-api-key': config['api_key'],
                'anthropic-version': '2023-06-01',
                'Content-Type': 'application/json'
            }
            
            payload = {
                'model': config['model'],
                'messages': [
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': temperature,
                'max_tokens': max_tokens
            }
            
            response = requests.post(
                config['url'],
                headers=headers,
                json=payload,
                timeout=config['timeout']
            )
            
            if response.status_code == 200:
                data = response.json()
                message = data['content'][0]['text']
                
                return {
                    'success': True,
                    'response': message.strip(),
                    'metadata': {
                        'model': config['model'],
                        'tokens': data.get('usage', {}).get('output_tokens', 0)
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"HTTP {response.status_code}: {response.text[:200]}"
                }
        
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    # ============ GESTIÓN DE STATS ============
    
    def get_stats(self) -> Dict:
        """Obtener estadísticas de todos los providers"""
        enabled_stats = [self.stats[k]['uptime_percentage'] for k, c in self.providers_config.items() if c['enabled']]
        total_calls = sum(p['total_calls'] for p in self.stats.values())
        successful_calls = sum(p['successful_calls'] for p in self.stats.values())
        failed_calls = sum(p['failed_calls'] for p in self.stats.values())
        return {
            'providers': self.stats,
            'global': {
                'total_calls': total_calls,
                'successful_calls': successful_calls,
                'failed_calls': failed_calls,
                'enabled_providers': sum(1 for c in self.providers_config.values() if c['enabled']),
                'avg_uptime': (sum(enabled_stats) / len(enabled_stats)) if enabled_stats else 0.0,
                'success_rate': ((successful_calls / total_calls) * 100) if total_calls else 0.0,
                'tokens_used': sum(p['tokens_used'] for p in self.stats.values())
            }
        }
    
    def get_provider_config(self, provider_id: str) -> Optional[Dict]:
        """Obtener configuración de un provider"""
        return self.providers_config.get(provider_id)
    
    def get_all_providers_config(self) -> Dict:
        """Obtener configuración de todos los providers (sin API keys)"""
        return {
            provider_id: {
                'name': config['name'],
                'model': config['model'],
                'enabled': config['enabled'],
                'local': config['local'],
                'priority': config['priority'],
                'has_api_key': bool(config['api_key'])
            }
            for provider_id, config in self.providers_config.items()
        }
    
    def update_api_key(self, provider_id: str, api_key: str) -> bool:
        """Actualizar API key de un provider"""
        if provider_id not in self.providers_config:
            return False

        cleaned_key = (api_key or "").strip()
        self.providers_config[provider_id]['api_key'] = cleaned_key or None
        if not self.providers_config[provider_id]['local']:
            self.providers_config[provider_id]['enabled'] = bool(cleaned_key)

        # Guardar en .env con alias de compatibilidad
        if provider_id == 'claude':
            self._update_env_file('CLAUDE_API_KEY', cleaned_key)
            self._update_env_file('ANTHROPIC_API_KEY', cleaned_key)
        elif not self.providers_config[provider_id]['local']:
            self._update_env_file(f'{provider_id.upper()}_API_KEY', cleaned_key)
        
        return True
    
    def toggle_provider(self, provider_id: str, enabled: bool) -> bool:
        """Habilitar/deshabilitar un provider"""
        if provider_id not in self.providers_config:
            return False
        cfg = self.providers_config[provider_id]
        if enabled and (not cfg['local']) and (not cfg['api_key']):
            return False
        if not enabled:
            currently_enabled = [pid for pid, c in self.providers_config.items() if c['enabled']]
            if provider_id in currently_enabled and len(currently_enabled) <= 1:
                return False
        self.providers_config[provider_id]['enabled'] = enabled
        return True
    
    def reset_stats(self, provider_id: Optional[str] = None):
        """Resetear estadísticas (de un provider o todos)"""
        if provider_id:
            if provider_id in self.stats:
                self.stats[provider_id] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'last_call': None,
                    'last_error': None,
                    'tokens_used': 0,
                    'uptime_percentage': 100.0
                }
        else:
            for provider_id in self.stats.keys():
                self.stats[provider_id] = {
                    'total_calls': 0,
                    'successful_calls': 0,
                    'failed_calls': 0,
                    'total_time': 0.0,
                    'avg_time': 0.0,
                    'last_call': None,
                    'last_error': None,
                    'tokens_used': 0,
                    'uptime_percentage': 100.0
                }
        
        self._save_stats()
    
    def _save_stats(self):
        """Guardar stats en archivo JSON"""
        try:
            stats_file = os.path.join(os.path.dirname(__file__), '..', 'ia_cascade_stats.json')
            with open(stats_file, 'w') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"⚠️ Error guardando stats: {e}")
    
    def _load_stats(self):
        """Cargar stats desde archivo JSON"""
        try:
            stats_file = os.path.join(os.path.dirname(__file__), '..', 'ia_cascade_stats.json')
            if os.path.exists(stats_file):
                with open(stats_file, 'r') as f:
                    loaded_stats = json.load(f)
                    # Merge con stats actuales
                    for provider_id, data in loaded_stats.items():
                        if provider_id in self.stats:
                            self.stats[provider_id].update(data)
        except Exception as e:
            print(f"⚠️ Error cargando stats: {e}")
    
    def _update_env_file(self, key: str, value: str):
        """Actualizar variable en archivo .env"""
        try:
            env_file = os.path.join(os.path.dirname(__file__), '..', '.env')
            
            # Leer contenido actual
            if os.path.exists(env_file):
                with open(env_file, 'r') as f:
                    lines = f.readlines()
            else:
                lines = []
            
            # Buscar y actualizar la línea
            found = False
            for i, line in enumerate(lines):
                if line.startswith(f'{key}='):
                    lines[i] = f'{key}={value}\n'
                    found = True
                    break
            
            # Si no existe, agregar al final
            if not found:
                lines.append(f'{key}={value}\n')
            
            # Guardar
            with open(env_file, 'w') as f:
                f.writelines(lines)
        
        except Exception as e:
            print(f"⚠️ Error actualizando .env: {e}")
    
    # ============ MÉTODOS DE COMPATIBILIDAD ============
    
    def chat(self, prompt: str, provider: str = 'cascade', temperature: float = 0.3) -> Dict:
        """Método de compatibilidad con AIService anterior"""
        if provider == 'cascade' or provider == 'auto':
            return self.consultar_cascade(prompt, temperature)
        else:
            return self.consultar_cascade(prompt, temperature, force_provider=provider)
    
    def analyze_document(self, text: str) -> Dict:
        """Analizar documento legal con IA"""
        prompt = f"""Eres un experto en análisis de documentos legales españoles.

DOCUMENTO A ANALIZAR:
{text[:5000]}

EXTRAE LA SIGUIENTE INFORMACIÓN:
1. TIPO DE DOCUMENTO (notificación_lexnet, demanda, sentencia, auto, decreto, providencia, contrato, escritura, otro)
2. CLIENTE (nombre completo de la persona principal)
3. FECHA (formato DD/MM/YYYY)
4. JUZGADO (si aplica)
5. NÚMERO DE PROCEDIMIENTO (si aplica)

RESPONDE SOLO CON JSON VÁLIDO sin explicaciones:
{{
  "tipo_documento": "...",
  "nombre_cliente": "...",
  "fecha_documento": "DD/MM/YYYY",
  "juzgado": "...",
  "numero_procedimiento": "..."
}}"""
        
        result = self.consultar_cascade(prompt, temperature=0.1)
        
        if result.get('success'):
            try:
                # Extraer JSON de la respuesta
                import re
                response_text = result.get('response', '')
                json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
                if json_match:
                    payload = json_match.group()
                    payload = payload.replace("```json", "").replace("```", "").strip()
                    metadata = json.loads(payload)
                    return {
                        'success': True,
                        'doctype': metadata.get('tipo_documento', 'documento'),
                        'metadata': metadata
                    }
            except Exception as e:
                print(f"⚠️ Error parseando respuesta JSON: {e}")
        
        return {
            'success': False,
            'doctype': 'documento',
            'metadata': {}
        }

    def health_check(self) -> Dict:
        """Estado operativo de providers (sin hacer llamadas de generación)."""
        providers = []
        for provider_id, cfg in self.providers_config.items():
            providers.append({
                'id': provider_id,
                'enabled': cfg['enabled'],
                'local': cfg['local'],
                'model': cfg['model'],
                'has_api_key': bool(cfg['api_key']),
                'priority': cfg['priority']
            })
        return {
            'success': True,
            'default_provider': self.default_provider,
            'enabled_count': sum(1 for p in providers if p['enabled']),
            'providers': providers
        }


# ============ INSTANCIA GLOBAL ============
ia_cascade = IACascadeService()


# ============ TESTING ============
if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🧪 TESTING IA CASCADE SERVICE")
    print("=" * 70 + "\n")
    
    # Test 1: Consulta simple con cascade
    print("\n📝 TEST 1: Consulta simple con cascade automático")
    result = ia_cascade.consultar_cascade(
        "¿Qué es el artículo 133 de la LEC?",
        temperature=0.3
    )
    print(f"\n✅ Resultado: {result.get('success')}")
    if result.get('success'):
        print(f"📄 Respuesta: {result.get('response', '')[:200]}...")
        print(f"🤖 Provider usado: {result.get('provider_used')}")
        print(f"⏱️  Tiempo: {result.get('time', 0):.2f}s")
    
    # Test 2: Forzar provider específico
    print("\n\n📝 TEST 2: Forzar provider específico (Groq)")
    result = ia_cascade.consultar_cascade(
        "Resume en 50 palabras qué es una demanda civil",
        temperature=0.3,
        force_provider='groq'
    )
    print(f"\n✅ Resultado: {result.get('success')}")
    
    # Test 3: Análisis de documento
    print("\n\n📝 TEST 3: Análisis de documento legal")
    sample_text = """
    AUTO DEL JUZGADO DE PRIMERA INSTANCIA Nº 5 DE MADRID
    
    PROCEDIMIENTO: Juicio Ordinario 123/2024
    DEMANDANTE: Juan Pérez García
    DEMANDADO: María López Rodríguez
    
    MADRID, 15 de enero de 2026
    
    Se acuerda...
    """
    result = ia_cascade.analyze_document(sample_text)
    print(f"\n✅ Resultado: {result.get('success')}")
    if result.get('success'):
        print(f"📋 Metadatos: {json.dumps(result.get('metadata', {}), indent=2, ensure_ascii=False)}")
    
    # Test 4: Mostrar stats
    print("\n\n📊 TEST 4: Estadísticas globales")
    stats = ia_cascade.get_stats()
    print(f"\n📈 STATS GLOBALES:")
    print(f"  Total llamadas: {stats['global']['total_calls']}")
    print(f"  Éxitos: {stats['global']['successful_calls']}")
    print(f"  Fallos: {stats['global']['failed_calls']}")
    print(f"  Uptime promedio: {stats['global']['avg_uptime']:.2f}%")
    
    print(f"\n📊 STATS POR PROVIDER:")
    for provider_id, provider_stats in stats['providers'].items():
        if provider_stats['total_calls'] > 0:
            print(f"  {provider_id.upper()}:")
            print(f"    - Llamadas: {provider_stats['total_calls']}")
            print(f"    - Éxitos: {provider_stats['successful_calls']}")
            print(f"    - Tiempo promedio: {provider_stats['avg_time']:.2f}s")
            print(f"    - Uptime: {provider_stats['uptime_percentage']:.2f}%")
    
    print("\n" + "=" * 70)
    print("✅ TESTING COMPLETADO")
    print("=" * 70 + "\n")
