import requests
import json

class OllamaService:
    def __init__(self, base_url='http://localhost:11434'):
        self.base_url = base_url
        self.model = 'lexdocs-legal'
        self.conversation_history = []
        
    def chat(self, prompt, context=''):
        """Enviar mensaje a Ollama con contexto jurídico"""
        try:
            full_prompt = self._build_legal_prompt(prompt, context)
            
            response = requests.post(
                f'{self.base_url}/api/generate',
                json={
                    'model': self.model,
                    'prompt': full_prompt,
                    'stream': False,
                    'options': {
                        'temperature': 0.3,
                        'top_p': 0.9,
                        'num_ctx': 8192,
                        'num_predict': 2000
                    }
                },
                timeout=90
            )
            
            if response.status_code == 200:
                result = response.json().get('response', 'Sin respuesta')
                
                self.conversation_history.append({
                    'user': prompt,
                    'assistant': result
                })
                
                return result
            else:
                return f"❌ Error del servidor: {response.status_code}"
                
        except requests.exceptions.ConnectionError:
            return """⚠️ **Ollama no está disponible**

Ollama debe estar corriendo en segundo plano.
Verifica con: `ollama list`

Si ves modelos listados, Ollama está funcionando correctamente."""
            
        except requests.exceptions.Timeout:
            return "⏱️ La consulta tardó demasiado. El modelo está procesando información compleja."
            
        except Exception as e:
            return f"❌ Error: {str(e)}"
    
    def _build_legal_prompt(self, prompt, context):
        """Construir prompt optimizado para análisis jurídico"""
        
        if context and len(context) > 100:
            # Análisis de documento con OCR
            return f"""**DOCUMENTO A ANALIZAR**
(Texto extraído mediante OCR - puede contener errores de reconocimiento)


{context[:4000]}

**CONSULTA DEL USUARIO**
{prompt}

**INSTRUCCIONES DE ANÁLISIS**
1. Lee el documento proporcionado
2. Identifica tipo de documento jurídico
3. Extrae información relevante a la consulta
4. Proporciona análisis jurídico fundamentado en derecho español
5. Cita artículos o normativa aplicable
6. Si detectas cláusulas problemáticas, señálalas
7. Concluye con recomendaciones prácticas

Responde de forma estructurada y profesional."""
        else:
            # Consulta general sin documento
            return f"""**CONSULTA LEGAL**

{prompt}

**INSTRUCCIONES**
Proporciona una respuesta fundamentada en derecho español vigente. Incluye:
- Normativa aplicable (leyes y artículos)
- Jurisprudencia relevante si procede
- Explicación clara y técnica
- Advertencias o consideraciones importantes

Responde de forma profesional y citando fuentes legales."""
    
    def reset_conversation(self):
        """Reiniciar historial de conversación"""
        self.conversation_history = []
    
    def get_available_models(self):
        """Listar modelos disponibles en Ollama"""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=3)
            if response.status_code == 200:
                models = response.json().get('models', [])
                return [model['name'] for model in models]
            return []
        except:
            return []
    
    def check_health(self):
        """Verificar si Ollama está corriendo"""
        try:
            response = requests.get(f'{self.base_url}/api/tags', timeout=2)
            return response.status_code == 200
        except:
            return False
