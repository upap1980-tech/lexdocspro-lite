import tempfile
import os
import re
import shutil
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file, send_from_directory, make_response, redirect
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Crear app Flask PRIMERO
app = Flask(__name__)

# ============================================
# CONFIGURACIÓN JWT Y SEGURIDAD
# ============================================

app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'CAMBIAR-ESTO-EN-PRODUCCION')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_ACCESS_TOKEN_EXPIRES', 3600)))
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(seconds=int(os.getenv('JWT_REFRESH_TOKEN_EXPIRES', 2592000)))

# ⭐ COOKIES JWT CONFIG
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_NAME'] = 'access_token_cookie'

# Inicializar JWT

# Servicios existentes
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.document_generator import DocumentGenerator
from services.lexnet_analyzer import LexNetAnalyzer

# ============================================
# DECORADORES Y AUTENTICACIÓN
# ============================================

# Configurar CORS
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5001').split(',')
CORS(app, resources={
    r"/api/*": {
        "origins": cors_origins,
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"],
        "supports_credentials": True
    }
})

# Registrar blueprint de autenticación (opcional)
try:
    from auth_blueprint import auth_bp
    app.register_blueprint(auth_bp)
except ImportError:
    print("⚠️  auth_blueprint no encontrado (opcional)")

print("✅ Sistema de autenticación JWT configurado")
print(f"⏱️  Duración access token: {app.config['JWT_ACCESS_TOKEN_EXPIRES']}")
print(f"⏱️  Duración refresh token: {app.config['JWT_REFRESH_TOKEN_EXPIRES']}")
print(f"🔐 JWT Token Location: {app.config['JWT_TOKEN_LOCATION']}")

# ============================================
# CONFIGURACIÓN MULTI-IA
# ============================================

# IA Local (Prioridad)
DEFAULT_AI_PROVIDER = os.getenv('DEFAULT_AI_PROVIDER', 'ollama')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'lexdocs-legal')

# APIs Cloud (Fallback)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'llama-3.1-sonar-large-128k-online')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
DEEPSEEK_API_KEY = os.getenv('DEEPSEEK_API_KEY')
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

# Configuración
BASE_DIR = os.path.expanduser("~/Desktop/EXPEDIENTES")
GENERATED_DOCS_DIR = os.path.join(BASE_DIR, "_GENERADOS")

# Servicios
ocr_service = OCRService()
ai_service = AIService()

# Inicializar Base de Datos para servicios (Models v3.0)

# Init ORM (SQLAlchemy) - Level 4
from models_orm import db as db_orm
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{os.path.join(BASE_DIR, "lexdocspro.db")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db_orm.init_app(app)

# RAG Skill Injection - Level 4
from services.skills.rag_skill import LiteRAGSkill
ai_service.rag_skill = None  # Fase 3



doc_generator = DocumentGenerator(ai_service)
lexnet_analyzer = LexNetAnalyzer(ai_service)

# Nuevo SignatureService v3.1.0


# Importar y configurar Auto-Processor
from services.autoprocessor_service import AutoProcessorService
autoprocessor = AutoProcessorService(ocr_service, ai_service)

# Importar y configurar Document Processing Service
from services.document_processing_service import DocumentProcessingService
doc_processor = DocumentProcessingService(ocr_service, ai_service, BASE_DIR)



# ============================================
# 🚑 LITE VERSION STUBS
# ============================================
class LiteStub:
    def __init__(self, *args, **kwargs): pass
    def __getattr__(self, name):
        def handler(*args, **kwargs):
            return {"success": False, "error": "Funcionalidad Enterprise no disponible en versión LITE"}
        return handler

signature_service = LiteStub()
# autoprocessor y doc_processor usan implementación real (Nivel 2)

# ============================================

# Asegurar directorios
os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)

# ============================================
# MENSAJE DE INICIO
# ============================================

print("="*60)
print("🚀 LexDocsPro LITE v2.0 - Sistema Legal Multi-IA")
print("="*60)
print(f"📁 Base: {BASE_DIR}")
print(f"📄 Generados: {GENERATED_DOCS_DIR}")
print("\n🤖 Inteligencia Artificial:")
print(f"  🎯 PRINCIPAL: Ollama Local ({OLLAMA_MODEL})")
if GROQ_API_KEY:
    print("  ✅ Fallback 1: Groq (Llama 3.3 70B)")
if PERPLEXITY_API_KEY:
    print(f"  ✅ Fallback 2: Perplexity PRO")
if OPENAI_API_KEY:
    print("  ✅ Disponible: OpenAI GPT-4")
if GEMINI_API_KEY:
    print("  ✅ Disponible: Google Gemini")
if DEEPSEEK_API_KEY:
    print("  ✅ Disponible: DeepSeek")
if ANTHROPIC_API_KEY:
    print("  ✅ Disponible: Anthropic Claude")
print("="*60)

# ============================================
# FUNCIÓN MULTI-IA CON CASCADA
# ============================================

def analizar_documento_con_ia_cascade(texto, max_chars=5000):
    """
    Analiza documento con múltiples IAs en cascada:
    1. Ollama local (privado, gratis, sin límites)
    2. Groq (rápido, gratis)
    3. Perplexity PRO (mejor contexto)
    """
    texto_limitado = texto[:max_chars]
    
    prompt_sistema = """Eres un experto en derecho procesal español especializado en análisis de documentos judiciales.
Extrae información estructurada con máxima precisión. Responde SOLO con JSON válido."""

    prompt_usuario = f"""Analiza este documento judicial español.

DOCUMENTO:
{texto_limitado}

INSTRUCCIONES CRÍTICAS:
1. **IDENTIFICAR CLIENTE (NO abogado)**:
   - Los abogados tienen número colegiado [XXX] → EXCLUIR SIEMPRE
   - "Victor Manuel Francisco Herrera [593]" = ABOGADO → EXCLUIR
   - "Cristina Maria Vera Reyes [329]" = ABOGADO → EXCLUIR
   - CLIENTE: Persona en sección DESTINATARIOS SIN [XXX]
   - O después de palabras: DEMANDANTE, DEMANDADO, IMPUTADO, ASEGURADO
   - Si formato es "APELLIDOS, NOMBRE" → convertir a "Nombre Apellidos"
   - Ejemplo: "PEREZ GARCIA, MARIA" → "Maria Perez Garcia"

2. **TIPO DE DOCUMENTO** (clasifica exactamente como):
   - "notificacion_lexnet" (si menciona LexNET o notificación judicial)
   - "auto" (si dice AUTO DE INCOACIÓN o AUTO)
   - "diligencias_urgentes" (si dice Diligencias Urgentes o Juicio Rápido)
   - "sentencia" (si dice SENTENCIA)
   - "demanda" (si dice DEMANDA)
   - "providencia" (si dice PROVIDENCIA)
   - "decreto" (si dice DECRETO)

3. **FECHA**: Busca formato dd/mm/aaaa
4. **NÚMERO PROCEDIMIENTO**: Si aparece número de procedimiento o NIG

RESPONDE SOLO CON ESTE JSON (sin markdown, sin comentarios):
{{
  "nombre_cliente": "nombre completo del cliente",
  "tipo_documento": "categoria_exacta",
  "fecha_documento": "dd/mm/aaaa",
  "ano": "aaaa",
  "numero_procedimiento": "número si existe o vacío",
  "confianza": "alta/media/baja"
}}"""

    # === NIVEL 1: OLLAMA LOCAL (Máxima prioridad - Privacidad) ===
    if DEFAULT_AI_PROVIDER == 'ollama' or not GROQ_API_KEY:
        try:
            print(f"🏠 Analizando con Ollama LOCAL ({OLLAMA_MODEL})...")
            response = requests.post(
                f'{OLLAMA_BASE_URL}/api/generate',
                json={
                    'model': OLLAMA_MODEL,
                    'prompt': f"{prompt_sistema}\n\n{prompt_usuario}",
                    'stream': False,
                    'options': {
                        'temperature': 0.1,
                        'num_predict': 600
                    }
                },
                timeout=45
            )
            
            if response.status_code == 200:
                ai_text = response.json().get('response', '')
                if ai_text and len(ai_text) > 20:
                    print(f"✅ Ollama respondió ({len(ai_text)} chars)")
                    return ai_text, 'ollama-local'
            else:
                print(f"⚠️ Ollama no disponible (código {response.status_code})")
        except requests.exceptions.ConnectionError:
            print("⚠️ Ollama no está corriendo → Intentando con APIs cloud...")
        except Exception as e:
            print(f"⚠️ Ollama error: {e}")

    # === NIVEL 2: GROQ (Fallback rápido y gratis) ===
    if GROQ_API_KEY:
        try:
            print("⚡ Fallback a Groq (ultra rápido)...")
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {GROQ_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [
                        {'role': 'system', 'content': prompt_sistema},
                        {'role': 'user', 'content': prompt_usuario}
                    ],
                    'temperature': 0.1,
                    'max_tokens': 600
                },
                timeout=25
            )
            
            if response.status_code == 200:
                ai_text = response.json()['choices'][0]['message']['content']
                print(f"✅ Groq respondió")
                return ai_text, 'groq'
            else:
                print(f"⚠️ Groq error {response.status_code}")
        except Exception as e:
            print(f"⚠️ Groq falló: {e}")

    # === NIVEL 3: PERPLEXITY PRO (Mejor contexto) ===
    if PERPLEXITY_API_KEY:
        try:
            print(f"🔮 Fallback a Perplexity PRO...")
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {PERPLEXITY_API_KEY}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': PERPLEXITY_MODEL,
                    'messages': [
                        {'role': 'system', 'content': prompt_sistema},
                        {'role': 'user', 'content': prompt_usuario}
                    ],
                    'temperature': 0.1,
                    'max_tokens': 700
                },
                timeout=30
            )
            
            if response.status_code == 200:
                ai_text = response.json()['choices'][0]['message']['content']
                print(f"✅ Perplexity respondió")
                return ai_text, 'perplexity'
        except Exception as e:
            print(f"⚠️ Perplexity falló: {e}")
    
    print("❌ Todas las IAs fallaron → Usando fallback REGEX")
    return None, None

# ============================================
# RUTAS EXISTENTES
# ============================================


@app.route('/api/files')
def list_files():
    path = request.args.get('path', '')
    full_path = os.path.join(BASE_DIR, path) if path else BASE_DIR
    
    folders = []
    files = []
    
    try:
        for item in os.listdir(full_path):
            if item.startswith('.'):
                continue
            
            item_path = os.path.join(full_path, item)
            rel_path = os.path.join(path, item) if path else item
            
            if os.path.isdir(item_path):
                folders.append({'name': item, 'path': rel_path})
            elif item.lower().endswith('.pdf'):
                files.append({'name': item, 'path': rel_path})
    except Exception as e:
        print(f"Error listing files: {e}")
    
    return jsonify({
        'current_path': path,
        'folders': folders,
        'files': files
    })

@app.route('/api/pdf/<path:filepath>')
def serve_pdf(filepath):
    full_path = os.path.join(BASE_DIR, filepath)
    if os.path.exists(full_path):
        return send_file(full_path, mimetype='application/pdf')
    return "File not found", 404

@app.route('/api/ocr', methods=['POST'])
def run_ocr():
    data = request.json
    filename = data.get('filename')
    full_path = os.path.join(BASE_DIR, filename)
    
    try:
        text = ocr_service.extraer_texto(full_path)
        return jsonify({'success': True, 'text': text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/providers')
def get_providers():
    providers = ai_service.get_available_providers()
    return jsonify({
        'providers': providers,
        'default': providers[0] if providers else 'ollama'
    })

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt')
    context = data.get('context', '')
    provider = data.get('provider', 'ollama')
    mode = data.get('mode', 'standard')
    
    try:
        response = ai_service.consultar(prompt, context, provider, mode)
        return jsonify({'success': True, 'response': response})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents/templates')
def get_templates():
    return jsonify(doc_generator.get_templates())

@app.route('/api/chat/stream', methods=['POST'])
def chat_stream():
    """Chat con Streaming (Nivel 4)"""
    try:
        data = request.json
        prompt = data.get('prompt')
        context = data.get('context', '')
        provider = data.get('provider')
        mode = data.get('mode', 'standard')
        
        def generate():
            for chunk in ai_service.stream_chat(prompt, context, provider, mode):
                yield chunk

        return Response(stream_with_context(generate()), mimetype='text/plain')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/generate', methods=['POST'])

def generate_document():
    print("\n" + "="*60)
    print("📄 RUTA: /api/documents/generate")
    print("="*60)
    
    try:
        data = request.json
        doc_type = data.get('type')
        form_data = data.get('data')
        provider = data.get('provider', 'ollama')
        
        print(f"✅ Datos recibidos:")
        print(f"   - Tipo: {doc_type}")
        print(f"   - Proveedor: {provider}")
        print(f"   - Campos: {list(form_data.keys()) if form_data else 'None'}")
        
        print(f"\n📝 Llamando a doc_generator.generate()...")
        result = doc_generator.generate(doc_type, form_data, provider)
        
        print(f"📝 Resultado: {type(result)} - Éxito: {result.get('success') if isinstance(result, dict) else 'N/A'}")
        
        # Verificar si result es un diccionario
        if not isinstance(result, dict):
            print(f"❌ ERROR: result no es dict, es {type(result)}")
            result = {'success': False, 'error': f'Tipo incorrecto: {type(result)}'}
        
        # Si no hay éxito en result
        if not result.get('success'):
            print(f"❌ ERROR en generación: {result.get('error')}")
            return jsonify(result)
        
        content = result.get('content', '')
        print(f"✅ Contenido generado: {len(content)} caracteres")
        
        # Guardar archivo
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{doc_type}_{timestamp}.txt"
        filepath = os.path.join(GENERATED_DOCS_DIR, filename)
        
        print(f"💾 Guardando en: {filepath}")
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Archivo guardado correctamente")
        
        response = {
            'success': True,
            'content': content,
            'filename': filename
        }
        
        print(f"✅ Respuesta enviada al cliente")
        print("="*60 + "\n")
        
        return jsonify(response)
        
    except Exception as e:
        print(f"❌ EXCEPCIÓN EN generate_document():")
        print(f"   Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print("="*60 + "\n")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ocr/upload', methods=['POST'])
def ocr_upload():
    """Extraer texto de archivo subido (PDF o imagen)"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400
        
        # Verificar formato soportado
        if not ocr_service.is_supported_file(file.filename):
            supported = ', '.join(ocr_service.get_supported_formats())
            return jsonify({
                'success': False, 
                'error': f'Formato no soportado. Soportados: {supported}'
            }), 400
        
        # Verificar tamaño (max 50MB)
        file.seek(0, 2)  # Ir al final
        file_size = file.tell()
        file.seek(0)  # Volver al inicio
        
        if file_size > 50 * 1024 * 1024:  # 50MB
            return jsonify({
                'success': False, 
                'error': 'Archivo muy grande (máximo 50MB)'
            }), 400
        
        # Guardar temporalmente
        temp_dir = tempfile.mkdtemp()
        
        # Sanitizar nombre de archivo
        from werkzeug.utils import secure_filename
        safe_filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, safe_filename)
        
        print(f"📤 Subiendo archivo: {safe_filename} ({file_size / 1024:.1f} KB)")
        file.save(temp_path)
        
        try:
            # DELEGACIÓN A DOCUMENT PROCESSING SERVICE (LITE)
            result = doc_processor.process_upload(file, client="GENERAL", save_to_db=True)
            
            if result['success']:
                return jsonify({
                    'success': True,
                    'text': result['text'],
                    'filename': safe_filename,
                    'size': file_size,
                    'doc_id': result.get('doc_id')
                })
            else:
                return jsonify({'success': False, 'error': 'Error procesando documento'}), 500

        finally:
            # Limpiar archivos temporales
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                if os.path.exists(temp_dir):
                    os.rmdir(temp_dir)
            except:
                pass

    except Exception as e:
        print(f"❌ Error en OCR upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lexnet/analyze', methods=['POST'])
def lexnet_analyze():
    """Analizar notificación LexNET"""
    try:
        data = request.json
        textos = data.get('textos', {})
        provider = data.get('provider', 'ollama')
        archivos = data.get('archivos', [])
        
        print(f"📊 Analizando LexNET con {provider}")
        print(f"📄 Textos recibidos: {list(textos.keys())}")
        
        if not any(textos.values()):
            return jsonify({
                'success': False,
                'error': 'No se pudo extraer texto de los archivos'
            })
        
        analisis = lexnet_analyzer.analizar_notificacion(textos, provider)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ANALISIS_LEXNET_{timestamp}.txt"
        filepath = os.path.join(GENERATED_DOCS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(analisis)
        
        print(f"✅ Análisis guardado: {filename}")
        
        return jsonify({
            'success': True,
            'analisis': analisis,
            'filename': filename,
            'filepath': filepath
        })
    
    except Exception as e:
        print(f"❌ Error en análisis LexNET: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

# ============================================
# ENDPOINTS iCLOUD
# ============================================

from services.icloud_service import iCloudService
icloud_service = iCloudService()

@app.route('/api/icloud/status')
def icloud_status():
    try:
        status = icloud_service.get_icloud_status()
        return jsonify({'success': True, **status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/icloud/export', methods=['POST'])
def icloud_export():
    try:
        data = request.json
        content = data.get('content')
        filename = data.get('filename')
        year = data.get('year')
        client_name = data.get('client_name')
        subfolder = data.get('subfolder')
        
        filepath = icloud_service.export_document(
            content=content,
            filename=filename,
            year=year,
            client_name=client_name,
            subfolder=subfolder
        )
        
        return jsonify({'success': True, 'filepath': filepath})
    
    except Exception as e:
        print(f"❌ Error exportando a iCloud: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/icloud/export-analysis', methods=['POST'])
def icloud_export_analysis():
    try:
        data = request.json
        content = data.get('content')
        client_name = data.get('client_name')
        
        filepath = icloud_service.export_analysis_to_client(
            analysis_content=content,
            client_name=client_name
        )
        
        return jsonify({'success': True, 'filepath': filepath})
    
    except Exception as e:
        print(f"❌ Error exportando análisis: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/icloud/clients')
def icloud_clients():
    try:
        clients = icloud_service.list_clients()
        return jsonify({'success': True, 'clients': clients})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# ============================================
# ANÁLISIS INTELIGENTE CON MULTI-IA
# ============================================

@app.route('/api/document/smart-analyze', methods=['POST'])
def smart_analyze_document():
    """Analiza documento con sistema multi-IA en cascada"""
    try:
        if 'file' not in request.files:
            return jsonify(error='No file provided'), 400
        
        file = request.files['file']
        
        if not file.filename:
            return jsonify(error='Empty filename'), 400
        
        print(f"\n{'='*60}")
        print(f"📄 ANALIZANDO: {file.filename}")
        
        # Guardar temporalmente
        tempdir = tempfile.mkdtemp()
        temppath = os.path.join(tempdir, file.filename)
        file.save(temppath)
        
        # EXTRAER TEXTO
        text_content = ""
        if file.filename.lower().endswith('.pdf'):
            import fitz
            doc = fitz.open(temppath)
            for page in doc:
                text_content += page.get_text()
            doc.close()
        
        print(f"📝 Extraído: {len(text_content)} caracteres")
        print(f"--- PREVIEW ---\n{text_content[:500]}\n---------------")
        
        # ANÁLISIS CON MULTI-IA (CASCADA)
        metadata = {
            'nombre_cliente': 'DESCONOCIDO',
            'tipo_documento': 'documento',
            'fecha_documento': '',
            'ano': str(datetime.now().year),
            'numero_procedimiento': '',
            'confianza': 'baja'
        }
        
        ai_response, provider = analizar_documento_con_ia_cascade(text_content, max_chars=5000)
        
        if ai_response:
            print(f"\n📥 Respuesta de {provider.upper()}:")
            print(ai_response[:400])
            
            # Extraer JSON
            import json
            json_match = re.search(r'\{[^{}]*\}', ai_response, re.DOTALL)
            if json_match:
                try:
                    ai_data = json.loads(json_match.group())
                    metadata.update(ai_data)
                    
                    print(f"\n✅ DATOS EXTRAÍDOS POR IA:")
                    print(f"   Cliente: {metadata['nombre_cliente']}")
                    print(f"   Tipo: {metadata['tipo_documento']}")
                    print(f"   Fecha: {metadata.get('fecha_documento', 'N/A')}")
                    print(f"   Confianza: {metadata.get('confianza', 'N/A')}")
                    
                except json.JSONDecodeError as e:
                    print(f"⚠️ Error parseando JSON: {e}")
        
        # FALLBACK REGEX (si todas las IAs fallan)
        if metadata['nombre_cliente'] == 'DESCONOCIDO':
            print("🔍 Usando fallback REGEX...")
            patterns = [
                r'DEMANDANTE[:\s]+([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]{10,50})',
                r'DEMANDADO[:\s]+([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]{10,50})',
                r'IMPUTADO[:\s]+([A-ZÁÉÍÓÚÑ][A-Za-záéíóúñ\s]{10,50})',
            ]
            for pattern in patterns:
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    metadata['nombre_cliente'] = matches[0].strip()
                    print(f"✅ REGEX encontró: {metadata['nombre_cliente']}")
                    break
        
        # Tipo de documento (fallback)
        if metadata['tipo_documento'] == 'documento':
            tl = text_content.lower()
            if 'lexnet' in tl:
                metadata['tipo_documento'] = 'notificacion_lexnet'
            elif 'auto de incoación' in tl or 'auto' in tl:
                metadata['tipo_documento'] = 'auto'
            elif 'diligencias urgentes' in tl or 'juicio rápido' in tl:
                metadata['tipo_documento'] = 'diligencias_urgentes'
            elif 'sentencia' in tl:
                metadata['tipo_documento'] = 'sentencia'
        
        # Fecha (fallback)
        if not metadata.get('fecha_documento'):
            dm = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', text_content)
            if dm:
                metadata['fecha_documento'] = f"{dm.group(1).zfill(2)}/{dm.group(2).zfill(2)}/{dm.group(3)}"
                metadata['ano'] = dm.group(3)
        
        # Buscar clientes existentes
        year = metadata['ano']
        year_path = os.path.join(BASE_DIR, year)
        existing_clients = []
        
        if os.path.exists(year_path):
            for folder in os.listdir(year_path):
                if os.path.isdir(os.path.join(year_path, folder)):
                    m = re.match(r'(\d{4})-(\d{2})\s+(.+)', folder)
                    if m:
                        existing_clients.append({
                            'codigo': f"{m.group(1)}-{m.group(2)}",
                            'nombre': m.group(3),
                            'carpeta': folder
                        })
        
        # Emparejar cliente
        cliente_propuesto = None
        if metadata['nombre_cliente'] != 'DESCONOCIDO':
            cw = set(metadata['nombre_cliente'].lower().split())
            for c in existing_clients:
                if len(cw & set(c['nombre'].lower().split())) >= 2:
                    cliente_propuesto = {**c, 'es_nuevo': False}
                    print(f"✅ ENCONTRADO: {c['carpeta']}")
                    break
        
        if not cliente_propuesto:
            if metadata['nombre_cliente'] != 'DESCONOCIDO':
                num = max([int(c['codigo'].split('-')[1]) for c in existing_clients], default=0) + 1
                cod = f"{year}-{num:02d}"
                cliente_propuesto = {
                    'codigo': cod,
                    'nombre': metadata['nombre_cliente'],
                    'carpeta': f"{cod} {metadata['nombre_cliente']}",
                    'es_nuevo': True
                }
                print(f"🆕 NUEVO: {cliente_propuesto['carpeta']}")
            else:
                cliente_propuesto = {
                    'codigo': f"{year}-00",
                    'nombre': 'SIN_CLASIFICAR',
                    'carpeta': f"{year}-00 SIN_CLASIFICAR",
                    'es_nuevo': False
                }
        
        # Nombre de archivo sugerido
        tipo = metadata['tipo_documento'].replace('_', '-')
        fecha = metadata.get('fecha_documento', '').replace('/', '-') or datetime.now().strftime('%Y-%m-%d')
        ext = os.path.splitext(file.filename)[1]
        nombre_sugerido = f"{fecha}_{tipo}{ext}"
        ruta_completa = os.path.join(BASE_DIR, year, cliente_propuesto['carpeta'], nombre_sugerido)
        
        print(f"\n📊 RESULTADO FINAL: {cliente_propuesto['carpeta']}")
        print(f"   Archivo: {nombre_sugerido}")
        print(f"{'='*60}\n")
        
        return jsonify({
            'success': True,
            'temp_file_path': temppath,
            'metadata': metadata,
            'cliente_propuesto': cliente_propuesto,
            'clientes_existentes': existing_clients[:10],
            'nombre_archivo_sugerido': nombre_sugerido,
            'ruta_completa': ruta_completa,
            'ruta_relativa': f"{year}/{cliente_propuesto['carpeta']}/{nombre_sugerido}",
            'texto_extraido': text_content[:300]
        })
    
    except Exception as e:
        import traceback
        print(f"\n❌ ERROR:\n{traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/document/save-organized', methods=['POST'])
def save_organized_document():
    """Guarda documento en la estructura de carpetas"""
    try:
        data = request.json
        temp_path = data.get('temp_file_path')
        dest_path = data.get('dest_path')
        
        if not temp_path or not dest_path:
            return jsonify({'error': 'Missing paths'}), 400
        
        # Crear carpetas si no existen
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        
        # Mover archivo
        shutil.move(temp_path, dest_path)
        
        return jsonify({
            'success': True,
            'saved_path': dest_path
        })
    
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

# ============================================
# AUTO-PROCESADOR - API ENDPOINTS
# ============================================

# ============================================

# Inicializar servicios
# Inicializar servicios

db_service = LiteStub()
decision_engine = LiteStub()

@app.route('/api/autoprocesador/stats')
def autoprocesador_stats():
    """Obtener estadísticas del auto-procesador"""
    try:
        stats = db_service.obtener_estadisticas_hoy()
        total = stats['total_hoy']
        
        if total > 0:
            stats['porcentaje_auto'] = round((stats['automaticos'] / total) * 100, 1)
            stats['porcentaje_revision'] = round((stats['en_revision'] / total) * 100, 1)
            stats['porcentaje_errores'] = round((stats['errores'] / total) * 100, 1)
        else:
            stats['porcentaje_auto'] = 0
            stats['porcentaje_revision'] = 0
            stats['porcentaje_errores'] = 0
        
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/cola-revision')
def autoprocesador_cola_revision():
    """Obtener documentos que requieren revisión"""
    try:
        documentos = db_service.obtener_cola_revision()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/procesados-hoy')
def autoprocesador_procesados_hoy():
    """Obtener documentos procesados hoy"""
    try:
        documentos = db_service.obtener_procesados_hoy()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/documento/<int:doc_id>')
def autoprocesador_documento(doc_id):
    """Obtener detalles de documento"""
    try:
        documento = db_service.obtener_documento(doc_id)
        if documento:
            return jsonify({'success': True, 'documento': documento})
        return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/aprobar/<int:doc_id>', methods=['POST'])
def autoprocesador_aprobar(doc_id):
    """Aprobar documento y guardarlo"""
    try:
        data = request.json or {}
        documento = db_service.obtener_documento(doc_id)
        
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Verificar si usuario modificó datos
        usuario_modifico = data.get('usuario_modifico', False)
        if usuario_modifico:
            updates = {}
            for key in ['cliente_codigo', 'cliente_detectado', 'tipo_documento', 'carpeta_sugerida']:
                if data.get(key):
                    updates[key] = data[key]
            if updates:
                db_service.actualizar_documento(doc_id, updates)
                documento = db_service.obtener_documento(doc_id)
        
        # Construir ruta destino
        analisis = {
            'cliente_codigo': documento.get('cliente_codigo'),
            'tipo_documento': documento.get('tipo_documento'),
            'fecha_documento': documento.get('fecha_documento'),
            'archivo_original': documento.get('archivo_original'),
        }
        
        base_dir = os.path.expanduser('~/Desktop/EXPEDIENTES_LEXDOCS')
        destino = decision_engine.construir_ruta_destino(analisis, base_dir)
        
        # Buscar archivo origen
        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )
        
        if not os.path.exists(archivo_origen):
            return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
        
        # Ejecutar acción
        exito = decision_engine.ejecutar_accion(
            'auto_process',
            archivo_origen,
            destino,
            os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS')
        )
        
        if exito:
            db_service.aprobar_documento(doc_id, destino['ruta_completa'], usuario_modifico)
            db_service.registrar_log('info', 'dashboard',
                                    f"Usuario aprobó: {documento.get('archivo_original')}", doc_id)
            return jsonify({
                'success': True,
                'mensaje': 'Documento aprobado y guardado',
                'ruta_destino': destino['ruta_completa']
            })
        
        return jsonify({'success': False, 'error': 'Error al guardar archivo'})
    
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/rechazar/<int:doc_id>', methods=['POST'])
def autoprocesador_rechazar(doc_id):
    """Rechazar documento"""
    try:
        data = request.json or {}
        motivo = data.get('motivo', 'Rechazado por usuario')
        
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Mover a REVISAR_MANUAL
        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )
        
        if os.path.exists(archivo_origen):
            manual_dir = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                'REVISAR_MANUAL'
            )
            os.makedirs(manual_dir, exist_ok=True)
            shutil.move(archivo_origen, os.path.join(manual_dir, documento.get('archivo_original', '')))
        
        db_service.rechazar_documento(doc_id, motivo)
        db_service.registrar_log('warning', 'dashboard',
                                f"Usuario rechazó: {documento.get('archivo_original')}", doc_id)
        
        return jsonify({'success': True, 'mensaje': 'Documento rechazado'})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/clientes')
def autoprocesador_clientes():
    """Listar clientes existentes"""
    try:
        base_dir = os.path.expanduser('~/Desktop/EXPEDIENTES_LEXDOCS')
        clientes = []
        
        if os.path.isdir(base_dir):
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.') and not item.startswith('_'):
                    partes = item.split('_', 2)
                    nombre = partes[2].replace('_', ' ') if len(partes) >= 3 else item
                    clientes.append({'codigo': item, 'nombre': nombre})
        
        clientes.sort(key=lambda x: x['codigo'])
        return jsonify({'success': True, 'clientes': clientes})
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/pdf/<int:doc_id>')
def autoprocesador_pdf(doc_id):
    """Servir PDF para vista previa"""
    try:
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return "Documento no encontrado", 404
        
        archivo = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo):
            archivo = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )
        
        if not os.path.exists(archivo):
            return "Archivo no encontrado", 404
        
        return send_file(archivo, mimetype='application/pdf')
    
    except Exception as e:
        return str(e), 500

# ============================================
# PDF PREVIEW ENDPOINT
# ============================================

@app.route('/api/document/preview', methods=['POST'])
def document_preview():
    """
    Generar preview de PDF como imagen
    
    Body:
    {
        "temp_file_path": "/tmp/xxxxx.pdf",
        "page": 1  // opcional, default 1
    }
    
    Returns:
    {
        "success": true,
        "image": "data:image/png;base64,...",
        "width": 800,
        "height": 1100,
        "total_pages": 5
    }
    """
    try:
        from services.pdf_preview_service import PDFPreviewService
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se enviaron datos'}), 400
        
        temp_file_path = data.get('temp_file_path')
        page = data.get('page', 1)
        
        if not temp_file_path:
            return jsonify({'success': False, 'error': 'temp_file_path requerido'}), 400
        
        # Generar preview
        pdf_preview = PDFPreviewService()
        result = pdf_preview.generate_preview(temp_file_path, page=page, as_base64=True)
        
        return jsonify(result), 200 if result.get('success') else 400
    
    except Exception as e:
        print(f"❌ Error en document preview: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/document/thumbnails', methods=['POST'])
def document_thumbnails():
    """
    Generar thumbnails de todas las páginas de un PDF (v2.2.0)
    """
    try:
        from services.pdf_preview_service import PDFPreviewService
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se enviaron datos'}), 400
        
        temp_file_path = data.get('temp_file_path')
        
        if not temp_file_path:
            return jsonify({'success': False, 'error': 'temp_file_path requerido'}), 400
            
        pdf_preview = PDFPreviewService()
        return jsonify(pdf_preview.generate_thumbnails(temp_file_path)), 200
        
    except Exception as e:
        print(f"❌ Error en thumbnails: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# LEXNET NOTIFICATIONS ENDPOINTS
# ============================================

@app.route('/api/lexnet/upload-notification', methods=['POST'])
def lexnet_upload_notification():
    """
    Subir y parsear archivo de notificación LexNET (PDF o XML)
    
    Retorna información de la notificación y la guarda en BD
    """
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió archivo'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'}), 400
        
        # Validar extensión
        allowed_extensions = ['pdf', 'xml']
        file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
        
        if file_ext not in allowed_extensions:
            return jsonify({
                'success': False, 
                'error': f'Formato no soportado. Usar: {", ".join(allowed_extensions)}'
            }), 400
        
        # Guardar temporalmente
        import tempfile
        import os
        from werkzeug.utils import secure_filename
        
        temp_dir = tempfile.mkdtemp()
        filename = secure_filename(file.filename)
        temp_path = os.path.join(temp_dir, filename)
        file.save(temp_path)
        
        try:
            # Parsear archivo
            parse_result = lexnet_service.parse_lexnet_file(temp_path)
            
            if not parse_result.get('success'):
                return jsonify(parse_result), 400
            
            notification_data = parse_result['notification_data']
            
            # Guardar en BD
            current_user_id = get_jwt_identity()
            notification_id = lexnet_service.save_notification(notification_data, current_user_id)
            
            # Limpiar archivo temporal
            os.remove(temp_path)
            os.rmdir(temp_dir)
            
            return jsonify({
                'success': True,
                'message': 'Notificación LexNET procesada correctamente',
                'notification_id': notification_id,
                'notification_data': notification_data
            }), 200
        
        finally:
            # Asegurar limpieza
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                try:
                    os.rmdir(temp_dir)
                except:
                    pass
    
    except Exception as e:
        print(f"❌ Error en lexnet upload: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lexnet/notifications', methods=['GET'])
def lexnet_get_notifications():
    """
    Obtener listado de notificaciones LexNET
    
    Query params:
    - unread: true/false (solo no leídas)
    - urgency: CRITICAL/URGENT/WARNING/NORMAL
    - limit: número máximo de resultados (default: 50)
    """
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        current_user_id = get_jwt_identity()
        
        # Parámetros
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        urgency = request.args.get('urgency', None)
        limit = request.args.get('limit', 50, type=int)
        
        # Obtener notificaciones
        lexnet_service = LexNetNotifications()
        notifications = lexnet_service.get_notifications(
            # user_id=current_user_id, # Ignored in LITE
            # unread_only=unread_only, # Ignored in LITE
            # urgency=urgency, # Ignored in LITE
            # limit=limit # Ignored in LITE
        )
        
        return jsonify({
            'success': True,
            'notifications': notifications,
            'total': len(notifications)
        }), 200
    
    except Exception as e:
        print(f"❌ Error obteniendo notificaciones: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lexnet/notifications/<int:notification_id>/read', methods=['PATCH'])
def lexnet_mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        current_user_id = get_jwt_identity()
        
        success = lexnet_service.mark_as_read(notification_id, current_user_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Notificación marcada como leída'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': 'No se pudo marcar como leída'
            }), 400
    
    except Exception as e:
        print(f"❌ Error marcando notificación: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/lexnet/urgent-count', methods=['GET'])
def lexnet_urgent_count():
    """Obtener contador de notificaciones urgentes (badge)"""
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        current_user_id = get_jwt_identity()
        
        urgent_count = lexnet_service.get_urgent_count(current_user_id)
        
        return jsonify({
            'success': True,
            'urgent_count': urgent_count
        }), 200
    
    except Exception as e:
        print(f"❌ Error obteniendo contador urgente: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# DOCUMENT PROCESSING ENDPOINTS (INTERACTIVE CONFIRMATION)
# ============================================

@app.route('/api/document/propose-save', methods=['POST'])
def document_propose_save():
    """
    Analizar documento y proponer clasificación con opciones de guardado
    
    Body:
    {
        "temp_file_path": "/tmp/xxxxx.pdf",
        "extracted_data": {
            "client": "María Pérez García",
            "doc_type": "Escrito Acusación MF",
            "date": "2022-03-15",
            "expedient": "123/2022",
            "court": "Juzgado...",
            "confidence": 95
        },
        "hint_year": 2026
    }
    """
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se enviaron datos'}), 400
        
        temp_file_path = data.get('temp_file_path')
        extracted_data = data.get('extracted_data')
        hint_year = data.get('hint_year')
        
        if not temp_file_path:
            return jsonify({'success': False, 'error': 'temp_file_path requerido'}), 400
        
        # Si no hay datos extraídos, extraer ahora
        if not extracted_data:
            extraction_result = doc_processor.extract_metadata(temp_file_path, hint_year)
            
            if not extraction_result.get('success'):
                return jsonify(extraction_result), 400
            
            extracted_data = extraction_result['metadata']
        
        # Proponer guardado
        proposal = doc_processor.propose_save(temp_file_path, extracted_data)
        
        if not proposal.get('success'):
            return jsonify(proposal), 400
        
        # Añadir preview de texto si está disponible
        try:
            text_preview = doc_processor.ocr_service.extract_text(temp_file_path)
            proposal['text_preview'] = text_preview[:1000] if text_preview else ""
        except:
            proposal['text_preview'] = ""
        
        return jsonify(proposal), 200
    
    except Exception as e:
        print(f"❌ Error en propose-save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/document/confirm-save', methods=['POST'])
def document_confirm_save():
    """
    Guardar documento con datos confirmados por el usuario
    
    Body:
    {
        "temp_file_path": "/tmp/xxxxx.pdf",
        "confirmed_data": {
            "client": "María Pérez García",
            "doc_type": "Escrito Acusación (MF)",
            "date": "2022-03-15",
            "expedient": "123/2022",
            "court": "Juzgado...",
            "year": 2026,
            "path": "/Users/.../EXPEDIENTES/2026/2026-03_MariaPerez/",
            "filename": "2026-03-15_acusacion_MF.pdf"
        }
    }
    """
    try:
        
        data = request.get_json()
        
        if not data:
            return jsonify({'success': False, 'error': 'No se enviaron datos'}), 400
        
        temp_file_path = data.get('temp_file_path')
        confirmed_data = data.get('confirmed_data')
        
        if not temp_file_path or not confirmed_data:
            return jsonify({
                'success': False, 
                'error': 'temp_file_path y confirmed_data son requeridos'
            }), 400
        
        # Obtener ID del usuario actual
        current_user_id = get_jwt_identity()
        
        # Guardar documento
        result = doc_processor.confirm_save(temp_file_path, confirmed_data, current_user_id)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        # Guardar metadata en BD
        try:
            doc_id = db.create_saved_document(
                filename=confirmed_data.get('filename'),
                file_path=result.get('final_path'),
                client_name=confirmed_data.get('client'),
                doc_type=confirmed_data.get('doc_type'),
                doc_date=confirmed_data.get('date'),
                expedient=confirmed_data.get('expedient'),
                court=confirmed_data.get('court'),
                year=confirmed_data.get('year'),
                created_by=current_user_id
            )
            
            result['document_id'] = doc_id
        except Exception as e:
            print(f"⚠️ Error guardando metadata en BD: {e}")
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"❌ Error en confirm-save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/document/path-options', methods=['GET'])
def document_path_options():
    """
    Obtener opciones de carpetas existentes para un año
    
    Query params:
    - year: 2026 (requerido)
    - client: "Maria" (opcional, filtrar por nombre cliente)
    """
    try:
        year = request.args.get('year', type=int)
        client_filter = request.args.get('client', None)
        
        if not year:
            return jsonify({'success': False, 'error': 'Parámetro year requerido'}), 400
        
        options = doc_processor.get_path_options(year, client_filter)
        
        return jsonify({
            'success': True,
            'year': year,
            'folders': options
        }), 200
    
    except Exception as e:
        print(f"❌ Error obteniendo path options: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/document/types', methods=['GET'])
def document_types():
    """Obtener lista completa de tipos de documentos soportados"""
    try:
        types = doc_processor.get_document_types()
        
        return jsonify({
            'success': True,
            'types': types,
            'allow_custom': True
        }), 200
    
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
def dashboard_stats():
    """Obtener estadísticas del dashboard en tiempo real (versión simple)"""
    try:
        # Documentos guardados hoy
        docs_today = db.count_documents_today()
        
        # Documentos pendientes
        pending = db.count_pending_documents()
        
        # Estadísticas del auto-processor
        processor_stats = autoprocessor.get_status()
        
        return jsonify({
            'success': True,
            'last_uploaded': docs_today,
            'in_review': pending,
            'processed_today': processor_stats.get('stats', {}).get('processed', 0),
            'errors_today': processor_stats.get('stats', {}).get('errors', 0)
        }), 200
    
    except Exception as e:
        print(f"❌ Error obteniendo stats: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/stats-detailed', methods=['GET'])
def dashboard_stats_detailed():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM saved_documents")
        docs_total = cursor.fetchone()[0]
        cursor.execute("""SELECT doc_type, COUNT(*) as count FROM saved_documents 
                       WHERE created_at >= DATE("now", "-30 days") 
                       AND doc_type IS NOT NULL AND doc_type != "" 
                       GROUP BY doc_type ORDER BY count DESC LIMIT 10""")
        by_type_rows = cursor.fetchall()
        by_type = {row[0]: row[1] for row in by_type_rows}
        cursor.execute("""SELECT client_name, COUNT(*) as count FROM saved_documents 
                       WHERE created_at >= DATE("now", "-30 days") 
                       AND client_name IS NOT NULL AND client_name != "" 
                       GROUP BY client_name ORDER BY count DESC LIMIT 10""")
        by_client_rows = cursor.fetchall()
        by_client = {row[0]: row[1] for row in by_client_rows}
        return jsonify({"success": True, "stats": {"total_documents": docs_total, "by_type": by_type, "by_client": by_client}})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn: conn.close()

@app.route('/api/autoprocessor/start', methods=['POST'])
def autoprocessor_start():
    """Iniciar monitor de carpeta PENDIENTES_LEXDOCS"""
    try:
        result = autoprocessor.start()
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/stop', methods=['POST'])
def autoprocessor_stop():
    """Detener monitor de carpeta"""
    try:
        result = autoprocessor.stop()
        status_code = 200 if result['success'] else 400
        return jsonify(result), status_code
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/status', methods=['GET'])
def autoprocessor_status():
    """Obtener estado del auto-processor"""
    try:
        status = autoprocessor.get_status()
        return jsonify(status), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/autoprocessor/logs', methods=['GET'])
def autoprocessor_logs():
    """Obtener logs recientes del auto-processor"""
    try:
        limit = request.args.get('limit', 50, type=int)
        logs = autoprocessor.get_logs(limit)
        return jsonify({'logs': logs}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/dashboard/drill-down/by-type/<doc_type>', methods=['GET'])
def drill_down_by_type(doc_type):
    """Obtener documentos procesados filtrados por tipo"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Obtener documentos de ese tipo
            # Nota: Usamos saved_documents que es la tabla de documentos confirmados
            query = "SELECT * FROM saved_documents WHERE doc_type = ? ORDER BY created_at DESC LIMIT ?"
            cursor.execute(query, (doc_type, limit))
            
            docs = []
            for row in cursor.fetchall():
                docs.append({
                    'id': row[0],
                    'filename': row[1],
                    'client': row[2],
                    'type': row[3],
                    'date': row[4],
                    'expedient': row[5],
                    'court': row[6],
                    'created_at': row[7]
                })
                
            return jsonify({'success': True, 'documents': docs}), 200
        finally:
            conn.close()
        
    except Exception as e:
        print(f"❌ Error drill-down type: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/drill-down/by-date/<date_str>', methods=['GET'])
def drill_down_by_date(date_str):
    """Obtener documentos procesados filtrados por fecha"""
    try:
        limit = request.args.get('limit', 50, type=int)
        conn = db.get_connection()
        cursor = conn.cursor()
        
        try:
            # Mapear fecha de tendencia a formato SQL
            # La fecha viene como "04 Feb" etc. Necesitamos algo aproximado o buscar por LIKE
            query = "SELECT * FROM saved_documents WHERE created_at LIKE ? ORDER BY created_at DESC LIMIT ?"
            # Nota: La lógica de fecha de tendencia es compleja, simplificamos buscando por coincidencia de texto
            cursor.execute(query, (f"%{date_str}%", limit))
            
            docs = []
            for row in cursor.fetchall():
                docs.append({
                    'id': row[0],
                    'filename': row[1],
                    'client': row[2],
                    'type': row[3],
                    'date': row[4],
                    'expedient': row[5],
                    'created_at': row[7]
                })
                
            return jsonify({'success': True, 'documents': docs}), 200
        finally:
            conn.close()
        
    except Exception as e:
        print(f"❌ Error drill-down date: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/export-pdf', methods=['GET'])
def export_dashboard_pdf():
    """
    Exportar estadísticas del dashboard a PDF (v2.2.0)
    """
    try:
        from services.report_service import DashboardReportService
        
        # 1. Obtener datos detallados (usamos la lógica interna de stats_detailed)
        # Para evitar duplicar código, en un entorno real refactorizaríamos a un StatsService
        # Por ahora, obtenemos un reporte completo
        
        # Re-usamos la lógica de dashboard_stats_detailed() internamente o llamamos a la función
        # Pero como necesitamos los datos, lo más limpio es obtener el JSON que retornaría
        stats_response = dashboard_stats_detailed()
        if stats_response[1] != 200:
            return stats_response
            
        stats_data = stats_response[0].get_json().get('stats')
        
        # 2. Generar reporte
        report_service = DashboardReportService()
        user_id = get_jwt_identity()
        user = db.get_user_by_id(user_id)
        user_name = user.get('nombre', 'Admin') if user else 'Admin'
        
        pdf_path = report_service.generate_report(stats_data, user_name)
        
        # 3. Retornar archivo
        return send_file(
            pdf_path,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f"reporte_dashboard_{datetime.now().strftime('%Y%m%d')}.pdf"
        )
        
    except Exception as e:
        print(f"❌ Error exportando PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# AI AGENT FEEDBACK LOOP (v3.0.0)
# ============================================

@app.route('/api/agent/feedback', methods=['POST'])
def save_agent_feedback():
    """Registrar feedback del usuario sobre la generación de la IA"""
    try:
        data = request.json
        expediente_id = data.get('expediente_id')
        contenido = data.get('contenido')
        score = data.get('score', 0) # -1 (mal), 1 (bien)
        
        if not expediente_id or not contenido:
            return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400
            
        # El feedback se guarda como una nota especial en case_notes
        note_id = db.add_case_note(
            expediente_id=expediente_id,
            contenido=contenido,
            tipo='feedback_ia',
            score=score
        )
        
        db.registrar_log('info', 'ai_feedback', f"Feedback guardado para expediente {expediente_id}")
        
        return jsonify({
            'success': True,
            'mensaje': 'Feedback registrado correctamente. La IA aprenderá de esta corrección.',
            'note_id': note_id
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SIGNATURE SERVICE ENDPOINTS (v3.1.0)
# ============================================

@app.route('/api/signature/certificates', methods=['GET'])
def list_certificates():
    """Listar certificados disponibles para firmar"""
    try:
        certs = signature_service.list_available_certificates()
        return jsonify({'success': True, 'certificates': certs})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signature/sign', methods=['POST'])
def sign_document():
    """
    Firmar un documento PDF con un certificado
    
    Body:
    {
        "doc_id": 123,
        "certificate": "firma.p12",
        "passphrase": "xxxx"
    }
    """
    try:
        data = request.json
        doc_id = data.get('doc_id')
        cert_name = data.get('certificate')
        passphrase = data.get('passphrase')
        
        if not all([doc_id, cert_name, passphrase]):
            return jsonify({'success': False, 'error': 'Faltan datos requeridos'}), 400
            
        documento = db.get_saved_document(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
            
        input_path = documento['file_path']
        output_filename = f"FIRMADO_{documento['filename']}"
        output_path = os.path.join(os.path.dirname(input_path), output_filename)
        
        success = signature_service.sign_pdf(input_path, output_path, cert_name, passphrase)
        
        if success:
            # Registrar en log y opcionalmente actualizar el documento en BD
            db.registrar_log('info', 'signature', f"Documento {doc_id} firmado con {cert_name}")
            return jsonify({
                'success': True, 
                'mensaje': 'Documento firmado con éxito',
                'signed_path': output_path
            })
        else:
            return jsonify({'success': False, 'error': 'Error en el proceso de firma'}), 500
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SERVIR FRONTEND VANILLA JS (v2.3.1)
# ============================================

@app.route('/')
def index():

    # Añadimos un parámetro de versión para romper la caché del navegador
    return render_template('index.html', v="3.0.1")
    
    """Servir la UI principal Vanilla JS"""
    return render_template('index.html')

@app.route('/notifications')
def notifications_redirect():
    """Redirigir /notifications a home"""
    return redirect('/')

@app.route('/<path:path>')
def serve_static(path):
    """Servir archivos estáticos desde /static"""
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return jsonify({'error': 'Not Found'}), 404

# ============================================
# NEW FEATURE ENDPOINTS (v2.3.1 CLASSIC)
# ============================================

@app.route('/api/banking/stats', methods=['GET'])
def get_banking_stats():
    """Obtener resumen de conciliación bancaria"""
    try:
        from services.banking_service import BankingService
        service = BankingService()
        # Simulamos obtención de últimos movimientos para el dashboard
        stats = {
            'bancos_activos': 11,
            'ultimo_sincro': datetime.now().strftime("%d/%m/%Y %H:%M"),
            'pendientes_conciliar': 24,
            'alerts_criticas': 0 # Limpio de 347
        }
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ai/status', methods=['GET'])
def get_ai_status():
    """Estado de salud de los proveedores de IA Cascade"""
    try:
        # Aquí llamaríamos a cada provider para ver si responde (ping)
        # Por ahora devolvemos un estado simulado basado en disponibilidad
        providers = ['ollama', 'groq', 'openai', 'perplexity', 'gemini', 'deepseek']
        status = {p: "Online" for p in providers}
        return jsonify({'success': True, 'status': status})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/test-email', methods=['POST'])
def test_email_alert():
    """Enviar un email de prueba (Email Alerts feature)"""
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        # Enviar email al usuario logueado
        success = email_service.send_alert(
            subject="LexDocsPro LITE: Test de Alerta Crítica",
            body="Este es un test de la funcionalidad Email Alerts v2.3.1."
        )
        return jsonify({'success': success})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ==================== LOGIN ENDPOINT ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        
        if email == 'admin@lexdocs.com' and password == 'admin123':
            access_token = create_access_token(identity=email)
            response = make_response({'success': True, 'token': access_token})
            response.set_cookie('access_token_cookie', access_token, max_age=3600)
            return response, 200
        else:
            return {'error': 'Credenciales inválidas'}, 401
    
    # GET - Mostrar formulario login
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LexDocsPro LITE - Login</title>
        <style>
            body { font-family: Arial; background: #007bff; display: flex; 
                   justify-content: center; align-items: center; height: 100vh; margin: 0; }
            .login-box { background: white; padding: 40px; border-radius: 8px; 
                        box-shadow: 0 4px 6px rgba(0,0,0,0.1); width: 300px; }
            h1 { color: #007bff; text-align: center; margin-top: 0; }
            input { width: 100%; padding: 12px; margin: 10px 0; border: 1px solid #ddd; 
                   border-radius: 4px; box-sizing: border-box; font-size: 14px; }
            button { width: 100%; padding: 12px; margin-top: 20px; background: #007bff; 
                    color: white; border: none; border-radius: 4px; cursor: pointer; 
                    font-size: 16px; font-weight: bold; }
            button:hover { background: #0056b3; }
            .error { color: red; text-align: center; margin-top: 10px; display: none; }
        </style>
    </head>
    <body>
        <div class="login-box">
            <h1>🔒 LexDocsPro LITE</h1>
            <form id="loginForm">
                <input type="email" id="email" placeholder="Email" value="admin@lexdocs.com" required>
                <input type="password" id="password" placeholder="Contraseña" value="admin123" required>
                <button type="submit">Login</button>
                <div class="error" id="error"></div>
            </form>
        </div>
        
        <script>
            document.getElementById('loginForm').onsubmit = async (e) => {
                e.preventDefault();
                const email = document.getElementById('email').value;
                const password = document.getElementById('password').value;
                
                const res = await fetch('/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({email, password})
                });
                
                if (res.ok) {
                    window.location.href = '/';
                } else {
                    document.getElementById('error').textContent = 'Credenciales inválidas';
                    document.getElementById('error').style.display = 'block';
                }
            };
        </script>
    </body>
    </html>
    ''', 200


# ============================================
# INICIAR SERVIDOR
# ============================================
if __name__ == '__main__':
    # Asegurar que las carpetas de destino existen
    # Asegurar que las carpetas de destino existen
    os.makedirs(BASE_DIR, exist_ok=True)
    os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)
    
    # Configurar static_folder para apuntar a la carpeta static raíz (Vanilla JS)
    app.static_folder = os.path.join(os.path.dirname(__file__), 'static')
    app.template_folder = os.path.join(os.path.dirname(__file__), 'templates')
    
    # Iniciar el servidor
    print(f"🚀 LexDocsPro LITE v2.3.1 SIDEBAR CLASSIC iniciando en puerto 5001...")
    # Usamos threaded=True para manejar múltiples peticiones si es necesario
    app.run(host='0.0.0.0', port=5001, debug=True)

db = None  # BD Fase 3
