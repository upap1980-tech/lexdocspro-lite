import tempfile
import io
import os
import re
import shutil
import uuid
import hashlib
import json
import secrets
from pathlib import Path
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, send_file, send_from_directory, make_response
from flask_cors import CORS
try:
    from flask_jwt_extended import (
        JWTManager,
        create_access_token,
        jwt_required,
        get_jwt_identity,
    )
    JWT_EXTENSION_AVAILABLE = True
except ImportError:
    JWT_EXTENSION_AVAILABLE = False

    class JWTManager:  # Fallback solo para entorno de estabilizacion P0
        def __init__(self, app=None):
            self.app = app

    def create_access_token(identity=None, additional_claims=None):
        del identity, additional_claims
        return "dev-token-no-jwt"

    def jwt_required(*args, **kwargs):
        del args, kwargs

        def decorator(fn):
            return fn

        return decorator

    def get_jwt_identity():
        return None
import requests
from dotenv import load_dotenv
# ============ IMPORTAR IA CASCADE SERVICE ============
from services.ia_cascade_service import ia_cascade

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

# ⭐ COOKIES + HEADER JWT CONFIG (fallback seguro)
app.config['JWT_TOKEN_LOCATION'] = os.getenv('JWT_TOKEN_LOCATION', 'cookies,headers').split(',')
app.config['JWT_COOKIE_SECURE'] = False
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_NAME'] = 'access_token_cookie'

# Inicializar JWT
jwt = JWTManager(app)

# ═══════════════════════════════════════════════════════════════
# INICIALIZAR DATABASE MANAGER (necesita app creada primero)
# ═══════════════════════════════════════════════════════════════
from models import DatabaseManager
from config import DB_PATH, EXPEDIENTES_DIR  # Importar DB_PATH
db = DatabaseManager(app)
print(f"🗄️  DatabaseManager inicializado: {DB_PATH}")

# ═══════════════════════════════════════════════════════════════
# SERVICIOS (ahora que db está listo)
# ═══════════════════════════════════════════════════════════════
from services.ocr_service import OCRService
from services.auto_processor_service import AutoProcessorService

from services.ai_service import AIService
from services.document_generator import DocumentGenerator
from services.lexnet_analyzer import LexNetAnalyzer
from services.business_skills_service import BusinessSkillsService
from services.ai_core_adapter_service import AICoreAdapterService

# ============================================
# DECORADORES Y AUTENTICACIÓN
# ============================================
from decorators import jwt_required_custom, abogado_or_admin_required, admin_required

# Configurar CORS
cors_origins = os.getenv('CORS_ORIGINS', 'http://localhost:5002').split(',')
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
except Exception as e:
    print(f"⚠️  auth_blueprint no disponible (opcional): {e}")

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
BASE_OCR_ROOT = os.path.expanduser("~/Desktop")
DEFAULT_OCR_PATHS = [
    "PROCESADOS_LEXDOCS",
    "PENDIENTES_LEXDOCS",
    "BACKUP_LEXDOCS",
    "ERRORES_LEXDOCS",
    "EXPEDIENTES_LEXDOCS",
]
BASE_DIR = os.path.join(BASE_OCR_ROOT, "PROCESADOS_LEXDOCS")
GENERATED_DOCS_DIR = os.path.join(BASE_DIR, "_GENERADOS")


def resolve_ocr_path(rel_path: str):
    """Return absolute path for an OCR file under any allowed root, else None."""
    if not rel_path:
        return BASE_DIR
    safe_rel = rel_path.lstrip("/").replace("..", "")
    for root in DEFAULT_OCR_PATHS:
        root_abs = os.path.join(BASE_OCR_ROOT, root)
        if safe_rel.startswith(root):
            suffix = os.path.relpath(safe_rel, root)
        else:
            suffix = safe_rel
        candidate = os.path.join(root_abs, suffix)
        try:
            if os.path.commonpath([candidate, root_abs]) == root_abs and os.path.exists(candidate):
                return candidate
        except Exception:
            continue
    return None

def find_file_in_roots(filename: str):
    """Buscar un archivo por nombre exacto en los roots permitidos."""
    if not filename:
        return None
    target = os.path.basename(filename)
    for root in DEFAULT_OCR_PATHS:
        root_abs = os.path.join(BASE_OCR_ROOT, root)
        if not os.path.exists(root_abs):
            continue
        for dirpath, _, files in os.walk(root_abs):
            if target in files:
                return os.path.join(dirpath, target)
    return None

# Servicios
ocr_service = OCRService()
ai_service = AIService()
ai_core_adapter = AICoreAdapterService()

# Inicializar Base de Datos para servicios (Models v3.0)
# Importar DatabaseManager o usar el existente
try:
    pass  # Bloque vacío
# COMENTADO -     db = DatabaseManager()
except ImportError:
    try:
        from models import db
    except ImportError:
        print("⚠️  No se pudo importar DatabaseManager ni db de models.py")
        db = None

# Módulo desactivado en versión LITE
# Módulo desactivado en versión LITE
# Módulo desactivado en versión LITE

doc_generator = DocumentGenerator(ai_service)
lexnet_analyzer = LexNetAnalyzer(ai_service)
business_skills_service = BusinessSkillsService(db)

# Nuevo SignatureService v3.1.0
from services.signature_service import SignatureService
signature_service = SignatureService()

# Importar y configurar Auto-Processor
from services.autoprocessor_service import AutoProcessorService
try:
    from services.ia_cascade_service import IACascadeService
except ImportError:
    IACascadeService = None

import os
PENDIENTES_DIR = os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS")
os.makedirs(PENDIENTES_DIR, exist_ok=True)

autoprocessor = AutoProcessorService(
    watch_dir=PENDIENTES_DIR,
    ocr_service=ocr_service if 'ocr_service' in locals() else None,
    ai_service=ai_service if 'ai_service' in locals() else None
)

# Iniciar automáticamente
if autoprocessor.start():
    print(f"✅ AutoProcessor iniciado: {PENDIENTES_DIR}")

# IA Cascade Service
try:
    if IACascadeService:
        ia_cascade = IACascadeService()
        print("✅ IA Cascade inicializado")
    else:
        ia_cascade = None
except Exception as e:
    print(f"⚠️  Error inicializando IA Cascade: {e}")
    ia_cascade = None

# Importar y configurar Document Processing Service
from services.document_processing_service import DocumentProcessingService
doc_processor = DocumentProcessingService(ocr_service, ai_service, BASE_DIR)

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

def analizar_documento_con_ia_cascade(texto, max_chars=5002):
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
    full_path = resolve_ocr_path(path)
    if not full_path:
        return jsonify({'success': False, 'error': 'Ruta no permitida o inexistente', 'roots': DEFAULT_OCR_PATHS}), 404
    
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
        'files': files,
        'roots': DEFAULT_OCR_PATHS
    })

@app.route('/api/pdf/<path:filepath>')
def serve_pdf(filepath):
    full_path = resolve_ocr_path(filepath)
    if full_path and os.path.exists(full_path):
        return send_file(full_path, mimetype='application/pdf')
    return "File not found", 404

@app.route('/api/ocr', methods=['POST'])
def run_ocr():
    data = request.get_json(silent=True) or {}
    filename = (data.get('filename') or '').strip()
    if not filename:
        return jsonify({
            'success': False,
            'error': 'filename requerido'
        }), 400

    full_path = resolve_ocr_path(filename)
    if not os.path.exists(full_path):
        return jsonify({
            'success': False,
            'error': 'Archivo no encontrado'
        }), 404

    try:
        text = ocr_service.extraer_texto(full_path)
        return jsonify({'success': True, 'text': text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

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


@app.route('/api/ai-core/health', methods=['GET'])
def ai_core_health_proxy():
    try:
        data = ai_core_adapter.health()
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/health/ocr', methods=['GET'])
def ai_core_health_ocr_proxy():
    try:
        data = ai_core_adapter.health_ocr()
        return jsonify({'success': True, 'data': data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/chat', methods=['POST'])
def ai_core_chat_proxy():
    data = request.get_json(silent=True) or {}
    message = data.get('message', '').strip()
    if not message:
        return jsonify({'success': False, 'error': 'message required'}), 400

    try:
        result = ai_core_adapter.chat(
            message=message,
            project_id=data.get('project_id', 'LexDocsPro-LITE'),
            case_id=data.get('case_id'),
            task_type=data.get('task_type', 'chat'),
            allow_cloud=bool(data.get('allow_cloud', False)),
            model=data.get('model'),
        )
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/rag/documents', methods=['GET'])
def ai_core_documents_proxy():
    project_id = request.args.get('project_id', 'LexDocsPro-LITE')
    case_id = request.args.get('case_id')
    try:
        result = ai_core_adapter.list_documents(project_id=project_id, case_id=case_id)
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/rag/search', methods=['POST'])
def ai_core_rag_search_proxy():
    data = request.get_json(silent=True) or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({'success': False, 'error': 'query required'}), 400

    try:
        result = ai_core_adapter.rag_search(
            project_id=data.get('project_id', 'LexDocsPro-LITE'),
            case_id=data.get('case_id'),
            query=query,
            top_k=int(data.get('top_k', 5)),
        )
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/rag/upload', methods=['POST'])
def ai_core_rag_upload_proxy():
    file = request.files.get('file')

    # multipart/form-data path (supports real file upload)
    if file is not None:
        project_id = request.form.get('project_id', 'LexDocsPro-LITE')
        case_id = request.form.get('case_id')
        document_id = request.form.get('document_id', file.filename or '')
        source = request.form.get('source', 'upload')
        source_url = request.form.get('source_url', '')
        page = request.form.get('page')

        try:
            temp_dir = tempfile.mkdtemp(prefix='ai_core_upload_')
            temp_path = Path(temp_dir) / (file.filename or 'upload.bin')
            file.save(str(temp_path))
            result = ai_core_adapter.rag_upload(
                project_id=project_id,
                case_id=case_id,
                document_id=document_id,
                source=source,
                source_url=source_url,
                page=page,
                file_path=str(temp_path),
            )
            return jsonify({'success': True, 'data': result}), 200
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 502
        finally:
            try:
                shutil.rmtree(temp_dir)
            except Exception:
                pass

    # JSON path (content text)
    data = request.get_json(silent=True) or {}
    content = (data.get('content') or '').strip()
    if not content:
        return jsonify({'success': False, 'error': 'content required (json) or file required (multipart)'}), 400

    try:
        result = ai_core_adapter.rag_upload(
            project_id=data.get('project_id', 'LexDocsPro-LITE'),
            case_id=data.get('case_id'),
            document_id=data.get('document_id', ''),
            source=data.get('source', 'upload'),
            source_url=data.get('source_url', ''),
            page=data.get('page'),
            content=content,
        )
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/rag/delete', methods=['POST'])
def ai_core_rag_delete_proxy():
    data = request.get_json(silent=True) or {}
    document_id = data.get('document_id')
    if document_id is None:
        return jsonify({'success': False, 'error': 'document_id required'}), 400

    try:
        result = ai_core_adapter.delete_document(
            project_id=data.get('project_id', 'LexDocsPro-LITE'),
            document_id=document_id,
            case_id=data.get('case_id'),
        )
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502


@app.route('/api/ai-core/rag/reindex', methods=['POST'])
def ai_core_rag_reindex_proxy():
    try:
        result = ai_core_adapter.reindex()
        return jsonify({'success': True, 'data': result}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 502

@app.route('/api/documents/templates')
def get_templates():
    return jsonify(doc_generator.get_templates())

@app.route('/api/business/jurisdictions', methods=['GET'])
def business_jurisdictions():
    try:
        return jsonify({
            "success": True,
            "jurisdictions": business_skills_service.list_jurisdictions()
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/business/templates', methods=['GET'])
def business_templates():
    try:
        jurisdiction = request.args.get("jurisdiction", "ES_GENERAL")
        return jsonify({
            "success": True,
            "jurisdiction": jurisdiction,
            "templates": business_skills_service.list_document_templates(jurisdiction)
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/business/strategy', methods=['POST'])
@abogado_or_admin_required
def business_strategy():
    try:
        data = request.get_json(silent=True) or {}
        strategy = business_skills_service.build_strategy(data)
        user_id = get_jwt_identity()
        critical, due_date, days_left = _business_deadline_criticality(strategy.get("deadline"))
        alert_sent = False
        if critical:
            try:
                from services.email_service import EmailService
                email_service = EmailService()
                ok, _ = email_service._validate_config()
                if ok:
                    alert_sent = email_service.send_alert(
                        subject="LexDocsPro: Deadline crítico detectado",
                        body=(
                            f"Jurisdicción: {strategy.get('jurisdiction')}\n"
                            f"Tipo: {strategy.get('doc_type')}\n"
                            f"Vencimiento: {due_date or 'N/A'}\n"
                            f"Días restantes: {days_left}\n"
                            f"Consulta: {data.get('query', '')}"
                        )
                    )
            except Exception:
                alert_sent = False

        history_id = _save_business_strategy_history(
            user_id=user_id,
            payload=data,
            strategy=strategy,
            critical=critical,
            deadline_date=due_date,
        )
        return jsonify({
            "success": True,
            "strategy": strategy,
            "history_id": history_id,
            "deadline_critical": critical,
            "deadline_days_left": days_left,
            "alert_sent": alert_sent
        }), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


def _ensure_business_strategy_history_table():
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS business_strategy_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                jurisdiction TEXT,
                doc_type TEXT,
                query TEXT,
                deadline_date TEXT,
                critical INTEGER,
                payload_json TEXT,
                strategy_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _business_deadline_criticality(deadline_dict):
    if not isinstance(deadline_dict, dict):
        return False, None, None
    dies_ad_quem = deadline_dict.get("dies_ad_quem")
    if not dies_ad_quem:
        return False, None, None
    try:
        due = datetime.strptime(dies_ad_quem, "%d/%m/%Y").date()
        days_left = (due - datetime.now().date()).days
        return days_left <= 2, due.isoformat(), days_left
    except Exception:
        return False, None, None


def _save_business_strategy_history(user_id, payload, strategy, critical, deadline_date):
    _ensure_business_strategy_history_table()
    conn = sqlite3.connect(str(DB_PATH))
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO business_strategy_history
            (user_id, jurisdiction, doc_type, query, deadline_date, critical, payload_json, strategy_json)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                str(user_id) if user_id is not None else None,
                strategy.get("jurisdiction"),
                strategy.get("doc_type"),
                payload.get("query"),
                deadline_date,
                1 if critical else 0,
                json.dumps(payload, ensure_ascii=False),
                json.dumps(strategy, ensure_ascii=False),
            ),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


def _strategy_to_text(strategy):
    steps = strategy.get("recommended_steps") or []
    deadline = strategy.get("deadline") or {}
    return (
        f"Estrategia Procesal\n"
        f"Jurisdiccion: {strategy.get('jurisdiction', '-')}\n"
        f"Tipo documental: {strategy.get('doc_type', '-')}\n"
        f"Vencimiento: {deadline.get('dies_ad_quem', 'N/A')}\n"
        f"Dia de gracia: {deadline.get('dia_gracia', 'N/A')}\n\n"
        f"Template Forense:\n{strategy.get('forensic_template', '')}\n\n"
        f"Prompt Base:\n{strategy.get('styled_prompt', '')}\n\n"
        f"Contexto RAG:\n{strategy.get('rag_context', '')}\n\n"
        f"Pasos recomendados:\n- " + "\n- ".join(steps)
    )


@app.route('/api/business/strategy/export', methods=['POST'])
@abogado_or_admin_required
def business_strategy_export():
    data = request.get_json(silent=True) or {}
    strategy = data.get("strategy") or {}
    if not strategy:
        return jsonify({"success": False, "error": "strategy requerido"}), 400

    export_format = (data.get("format") or "pdf").lower()
    client_name = (data.get("client_name") or "GENERAL").strip().replace("/", "_")
    year = int(data.get("year") or datetime.now().year)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_path = Path(EXPEDIENTES_DIR) / str(year) / client_name / "ESTRATEGIAS"
    base_path.mkdir(parents=True, exist_ok=True)
    strategy_text = _strategy_to_text(strategy)

    if export_format == "txt":
        out_file = base_path / f"Estrategia_{strategy.get('doc_type', 'general')}_{ts}.txt"
        out_file.write_text(strategy_text, encoding="utf-8")
        return jsonify({"success": True, "format": "txt", "path": str(out_file)}), 200

    # PDF por defecto
    out_file = base_path / f"Estrategia_{strategy.get('doc_type', 'general')}_{ts}.pdf"
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        c = canvas.Canvas(str(out_file), pagesize=A4)
        w, h = A4
        y = h - 50
        for line in strategy_text.split("\n"):
            c.drawString(40, y, line[:110])
            y -= 16
            if y < 40:
                c.showPage()
                y = h - 50
        c.save()
        return jsonify({"success": True, "format": "pdf", "path": str(out_file)}), 200
    except Exception as e:
        txt_fallback = base_path / f"Estrategia_{strategy.get('doc_type', 'general')}_{ts}.txt"
        txt_fallback.write_text(strategy_text, encoding="utf-8")
        return jsonify({
            "success": True,
            "warning": f"No se pudo generar PDF ({e}), exportado TXT",
            "format": "txt",
            "path": str(txt_fallback)
        }), 200


@app.route('/api/business/strategy/history', methods=['GET'])
@abogado_or_admin_required
def business_strategy_history():
    limit = max(1, min(200, int(request.args.get("limit", 50))))
    from_date = (request.args.get("from_date") or "").strip()
    to_date = (request.args.get("to_date") or "").strip()
    user_filter = (request.args.get("user_id") or "").strip()

    _ensure_business_strategy_history_table()
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()
        where_clauses = []
        params = []

        if from_date:
            where_clauses.append("DATE(created_at) >= DATE(?)")
            params.append(from_date)
        if to_date:
            where_clauses.append("DATE(created_at) <= DATE(?)")
            params.append(to_date)
        if user_filter:
            where_clauses.append("LOWER(COALESCE(user_id,'')) LIKE ?")
            params.append(f"%{user_filter.lower()}%")

        where_sql = ""
        if where_clauses:
            where_sql = "WHERE " + " AND ".join(where_clauses)

        query_sql = f"""
            SELECT
                id,
                user_id,
                jurisdiction,
                doc_type,
                query,
                deadline_date,
                critical,
                payload_json,
                strategy_json,
                created_at
            FROM business_strategy_history
            {where_sql}
            ORDER BY id DESC
            LIMIT ?
        """
        params.append(limit)
        cur.execute(query_sql, tuple(params))
        items = [dict(r) for r in cur.fetchall()]

        for item in items:
            for key in ("payload_json", "strategy_json"):
                raw = item.get(key)
                if raw:
                    try:
                        item[key] = json.loads(raw)
                    except Exception:
                        pass

        return jsonify({"success": True, "items": items}), 200
    finally:
        conn.close()

@app.route('/api/documents/generate', methods=['POST'])
@abogado_or_admin_required
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
@jwt_required_custom
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
            # Extraer texto
            print(f"🔍 Extrayendo texto...")
            text = ocr_service.extract_text(temp_path)
            
            print(f"✅ Texto extraído: {len(text)} caracteres")
            
            return jsonify({
                'success': True,
                'text': text,
                'filename': safe_filename,
                'size': file_size
            })
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
@abogado_or_admin_required
def lexnet_analyze():
    """Analizar notificación LexNET"""
    try:
        data = request.json
        textos = data.get('textos', {})
        provider = data.get('provider', 'ollama')
        archivos = data.get('archivos', [])
        nombre = data.get('nombre')  # compat contrato frontend legacy
        
        print(f"📊 Analizando LexNET con {provider}")
        print(f"📄 Textos recibidos: {list(textos.keys())}")
        if nombre:
            print(f"👤 Nombre recibido: {nombre}")
        
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
@abogado_or_admin_required
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
@jwt_required_custom
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
        
        # EXTRAER TEXTO (con fallback para no romper flujo si falla PyMuPDF)
        text_content = ""
        if file.filename.lower().endswith('.pdf'):
            extraction_errors = []

            # 1) PyMuPDF (rápido cuando está sano)
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(temppath)
                for page in doc:
                    text_content += page.get_text() or ""
                doc.close()
            except Exception as e:
                extraction_errors.append(f"fitz: {e}")

            # 2) pypdf/PyPDF2 fallback
            if not text_content.strip():
                try:
                    try:
                        from pypdf import PdfReader
                    except Exception:
                        from PyPDF2 import PdfReader
                    reader = PdfReader(temppath)
                    chunks = []
                    for p in reader.pages:
                        chunks.append(p.extract_text() or "")
                    text_content = "\n".join(chunks)
                except Exception as e:
                    extraction_errors.append(f"pypdf: {e}")

            # 3) OCR service fallback (último recurso)
            if not text_content.strip():
                try:
                    text_content = doc_processor.ocr_service.extract_text(temppath) or ""
                except Exception as e:
                    extraction_errors.append(f"ocr_service: {e}")

            if not text_content.strip():
                return jsonify({
                    'success': False,
                    'error': 'No se pudo extraer texto del PDF',
                    'detail': ' | '.join(extraction_errors)[:1500]
                }), 422
        
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
        
        ai_response, provider = analizar_documento_con_ia_cascade(text_content, max_chars=5002)
        
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

# Servicios opcionales
try:
    from services.db_service import DatabaseService
    from services.decision_engine import DecisionEngine
    db_service = DatabaseService()
    decision_engine = DecisionEngine()
    print("✅ Servicios opcionales cargados")
except ImportError as e:
    print(f"⚠️  Servicios opcionales no disponibles: {e}")
    db_service = None
    decision_engine = None

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
@abogado_or_admin_required
def autoprocesador_aprobar(doc_id):
    """Aprobar documento y guardarlo"""
    try:
        data = request.json or {}
        _cliente_codigo = data.get('cliente_codigo')  # compat skill contrato
        _tipo_documento = data.get('tipo_documento')  # compat skill contrato
        del _cliente_codigo, _tipo_documento
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
@jwt_required_custom
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
@jwt_required_custom
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
@abogado_or_admin_required
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
            lexnet_service = LexNetNotifications(db_manager=db)
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
@jwt_required_custom
def lexnet_get_notifications():
    """
    Obtener listado de notificaciones LexNET
    
    Query params:
    - unread: true/false (solo no leídas)
    - urgency: CRITICAL/URGENT/WARNING/NORMAL
    - limit: número máximo de resultados (default: 50)
    - case_type: tipo procesal normalizado (ej: JUICIO_VERBAL)
    - date_from: fecha inicio YYYY-MM-DD
    - date_to: fecha fin YYYY-MM-DD
    - procedure_number: filtro parcial por número procedimiento
    """
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        current_user_id = get_jwt_identity()
        
        # Parámetros
        unread_only = request.args.get('unread', 'false').lower() == 'true'
        urgency = request.args.get('urgency', None)
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        case_type = request.args.get('case_type', None)
        date_from = request.args.get('date_from', None)
        date_to = request.args.get('date_to', None)
        procedure_number = request.args.get('procedure_number', None)
        
        # Obtener notificaciones
        lexnet_service = LexNetNotifications(db_manager=db)
        notifications = lexnet_service.get_notifications(
            user_id=current_user_id,
            unread_only=unread_only,
            urgency=urgency,
            limit=limit,
            offset=offset,
            case_type=case_type,
            date_from=date_from,
            date_to=date_to,
            procedure_number=procedure_number
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
@jwt_required_custom
def lexnet_mark_notification_read(notification_id):
    """Marcar notificación como leída"""
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        current_user_id = get_jwt_identity()
        
        lexnet_service = LexNetNotifications(db_manager=db)
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
@jwt_required_custom
def lexnet_urgent_count():
    """Obtener contador de notificaciones urgentes (badge)"""
    try:
        from services.lexnet_notifications import LexNetNotifications
        
        current_user_id = get_jwt_identity()
        
        lexnet_service = LexNetNotifications(db_manager=db)
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
@jwt_required_custom
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

        # Persistir propuesta en cola para completar ciclo E2E en confirm-save.
        try:
            pending_id = db.create_pending_document(
                temp_file_path=temp_file_path,
                original_filename=os.path.basename(temp_file_path),
                extracted_data=extracted_data,
                proposed_data=proposal.get('proposal') or {},
                status='proposed'
            )
            proposal['pending_document_id'] = pending_id
            proposal['proposal_id'] = pending_id  # alias de compatibilidad
        except Exception as e:
            print(f"⚠️ Error guardando propuesta en pending_documents: {e}")
            proposal['pending_document_id'] = None
        
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
@abogado_or_admin_required
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
        pending_document_id = data.get('pending_document_id') or data.get('proposal_id')
        
        if not confirmed_data:
            return jsonify({
                'success': False, 
                'error': 'confirmed_data es requerido'
            }), 400

        if pending_document_id and not temp_file_path:
            pending_doc = db.get_pending_document(int(pending_document_id))
            if not pending_doc:
                return jsonify({'success': False, 'error': 'pending_document_id no encontrado'}), 404
            temp_file_path = pending_doc.get('temp_file_path')

        if not temp_file_path:
            return jsonify({'success': False, 'error': 'temp_file_path es requerido'}), 400
        
        # Obtener ID del usuario actual
        current_user_id = get_jwt_identity()
        
        # Guardar documento
        result = doc_processor.confirm_save(temp_file_path, confirmed_data, current_user_id)
        
        if not result.get('success'):
            return jsonify(result), 400
        
        # Guardar metadata en BD
        try:
            doc_id = db.create_saved_document(
                filename=confirmed_data.get('filename') or os.path.basename(result.get('final_path', '')),
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
            if pending_document_id:
                db.mark_pending_document_confirmed(int(pending_document_id), current_user_id)
                result['pending_document_id'] = int(pending_document_id)
        except Exception as e:
            print(f"⚠️ Error guardando metadata en BD: {e}")
        
        return jsonify(result), 200
    
    except Exception as e:
        print(f"❌ Error en confirm-save: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/document/path-options', methods=['GET'])
@jwt_required_custom
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

@app.route('/api/document/saved/<int:doc_id>', methods=['GET'])
@jwt_required_custom
def document_saved_detail(doc_id):
    """Obtener detalle de documento guardado (ruta final E2E)."""
    try:
        document = db.get_saved_document(doc_id)
        if not document:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        return jsonify({'success': True, 'document': document}), 200
    except Exception as e:
        print(f"❌ Error consultando documento guardado {doc_id}: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/document/saved', methods=['GET'])
@jwt_required_custom
def document_saved_list():
    """Listar documentos guardados recientes (ruta final E2E)."""
    try:
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        docs = db.list_saved_documents(limit=limit or 50, offset=offset or 0)
        return jsonify({'success': True, 'documents': docs, 'total': len(docs)}), 200
    except Exception as e:
        print(f"❌ Error listando documentos guardados: {str(e)}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """Obtener estadísticas del dashboard en tiempo real"""
    try:
        from datetime import date
        import sqlite3
        
        # Usar DB_PATH importado de config
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 1. Documentos procesados hoy
        today = date.today().isoformat()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM saved_documents 
            WHERE DATE(created_at) = ?
        """, (today,))
        docs_today = cursor.fetchone()[0] or 0
        
        # 2. Documentos en revisión (pendientes)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'pending'
        """)
        pending = cursor.fetchone()[0] or 0
        
        # 3. Errores (rechazados hoy)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'rejected' 
            AND DATE(created_at) = ?
        """, (today,))
        errores = cursor.fetchone()[0] or 0
        
        # 4. Alertas LexNET urgentes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM notifications 
            WHERE urgency IN ('CRITICAL', 'URGENT') 
            AND read = 0
        """)
        alertas = cursor.fetchone()[0] or 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'procesos_hoy': docs_today,
            'en_revision': pending,
            'errores': errores,
            'alertas': alertas
        }), 200
    
    except Exception as e:
        print(f"❌ Error obteniendo stats: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Devolver valores por defecto
        return jsonify({
            'success': True,
            'procesos_hoy': 0,
            'en_revision': 0,
            'errores': 0,
            'alertas': 0
        }), 200


@app.route('/api/dashboard/stats-detailed', methods=['GET'])
@jwt_required()
def dashboard_stats_detailed():
    conn = None
    try:
        from datetime import date, timedelta
        conn = db.get_connection()
        cursor = conn.cursor()

        # Totales
        cursor.execute("SELECT COUNT(*) FROM saved_documents")
        docs_total = cursor.fetchone()[0]

        # Distribución por tipo (últimos 30 días)
        cursor.execute("""
            SELECT doc_type, COUNT(*) as count
            FROM saved_documents 
            WHERE created_at >= DATE('now', '-30 days') 
              AND doc_type IS NOT NULL AND doc_type != '' 
            GROUP BY doc_type ORDER BY count DESC LIMIT 10
        """)
        by_type_rows = cursor.fetchall()
        by_type = {row[0]: row[1] for row in by_type_rows}

        # Distribución por cliente (últimos 30 días)
        cursor.execute("""
            SELECT client_name, COUNT(*) as count
            FROM saved_documents 
            WHERE created_at >= DATE('now', '-30 days') 
              AND client_name IS NOT NULL AND client_name != '' 
            GROUP BY client_name ORDER BY count DESC LIMIT 10
        """)
        by_client_rows = cursor.fetchall()
        by_client = {row[0]: row[1] for row in by_client_rows}

        # Tendencia últimos 7 días
        today = date.today()
        last7 = [(today - timedelta(days=i)).isoformat() for i in range(6, -1, -1)]
        placeholders = ",".join(["?"] * len(last7))
        cursor.execute(
            f"""
            SELECT DATE(created_at) as d, COUNT(*) as c
            FROM saved_documents
            WHERE DATE(created_at) IN ({placeholders})
            GROUP BY DATE(created_at)
            """,
            last7,
        )
        map_counts = {row[0]: row[1] for row in cursor.fetchall()}
        trends_labels = [d[8:10] + "/" + d[5:7] for d in last7]  # dd/mm
        trends_values = [map_counts.get(d, 0) for d in last7]

        # Documentos recientes (ultimos 10)
        cursor.execute("""
            SELECT filename, created_at 
            FROM saved_documents
            ORDER BY datetime(created_at) DESC
            LIMIT 10
        """)
        rows_recent = cursor.fetchall()
        recent_docs = [
            {'name': r[0], 'time': r[1]} for r in rows_recent
        ]

        # Alertas recientes (ultimo 10)
        cursor.execute("""
            SELECT title, created_at, urgency
            FROM notifications
            ORDER BY datetime(created_at) DESC
            LIMIT 10
        """)
        rows_alerts = cursor.fetchall()
        recent_alerts = [
            {'title': r[0], 'time': r[1], 'urgency': r[2]} for r in rows_alerts
        ]

        # Compatibilidad con frontend antiguo y nuevo
        today_total = sum(trends_values[-1:]) if trends_values else 0
        week_total = sum(trends_values[-7:]) if trends_values else 0
        month = docs_total
        return jsonify({
            "success": True,
            "stats": {
                "total_documents": docs_total,
                "by_type": by_type,
                "by_client": by_client
            },
            "kpis": {
                "today": today_total,
                "week": week_total,
                "month": month
            },
            "trends": {
                "labels": trends_labels,
                "values": trends_values
            },
            "recent_docs": recent_docs,
            "recent_alerts": recent_alerts,
            "logs": []
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500
    finally:
        if conn: conn.close()


# ═══════════════════════════════════════════════════════════════
# AUTO-PROCESSOR ENDPOINTS (v3.2 - FIXED)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/autoprocessor/status', methods=['GET'])
@jwt_required_custom
def autoprocessor_status():
    """Obtener estado del auto-procesador"""
    try:
        status = autoprocessor.get_status()
        return jsonify({'success': True, 'status': status}), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/start', methods=['POST'])
@jwt_required_custom
def autoprocessor_start():
    """Iniciar el auto-procesador"""
    try:
        result = autoprocessor.start()
        return jsonify({
            'success': True,
            'message': '✅ Iniciado' if result else '⚠️ Ya estaba iniciado'
        }), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/stop', methods=['POST'])
@jwt_required_custom
def autoprocessor_stop():
    """Detener el auto-procesador"""
    try:
        result = autoprocessor.stop()
        return jsonify({
            'success': True,
            'message': '🛑 Detenido' if result else '⚠️ Ya estaba detenido'
        }), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/scan', methods=['POST'])
@jwt_required_custom
def autoprocessor_scan():
    """Escanear y procesar archivos"""
    try:
        files = autoprocessor.scan_existing_files()
        
        if not files:
            return jsonify({
                'success': True,
                'processed': 0,
                'message': '✅ No hay archivos'
            }), 200
        
        import threading
        for f in files:
            threading.Thread(target=autoprocessor.process_file, args=(f,), daemon=True).start()
        
        return jsonify({
            'success': True,
            'processed': len(files),
            'message': f'✅ {len(files)} archivo(s) en proceso',
            'status': 'running' if autoprocessor.is_running else 'stopped'
        }), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/reset', methods=['POST'])
@jwt_required_custom
def autoprocessor_reset():
    """Resetear estadísticas"""
    try:
        autoprocessor.stats = {
            'processed': 0,
            'errors': 0,
            'pending': 0,
            'last_processed': None,
            'start_time': autoprocessor.stats.get('start_time')
        }
        autoprocessor.processing_queue = []
        
        return jsonify({
            'success': True,
            'message': '✅ Estadísticas reseteadas'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/log', methods=['GET'])
@jwt_required_custom
def autoprocessor_log():
    """Obtener log de procesamiento con trazabilidad"""
    try:
        limit = request.args.get('limit', 50, type=int)
        log = autoprocessor.get_processing_log(limit)
        
        return jsonify({
            'success': True,
            'log': log,
            'total': len(log)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/file', methods=['GET'])
@jwt_required_custom
def autoprocessor_file():
    """Servir archivos procesados/backup/errores de forma segura."""
    try:
        path = request.args.get('path')
        preview = request.args.get('preview', '0') == '1'
        if not path:
            return jsonify({'success': False, 'error': 'path requerido'}), 400
        allowed_roots = [
            os.path.expanduser("~/Desktop/PROCESADOS"),
            os.path.expanduser("~/Desktop/BACKUP_LEXDOCS"),
            os.path.expanduser("~/Desktop/ERRORES_LEXDOCS"),
            os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS"),
        ]
        abs_path = os.path.abspath(path)
        if not any(abs_path.startswith(root) for root in allowed_roots):
            return jsonify({'success': False, 'error': 'Path no permitido'}), 403
        if not os.path.exists(abs_path):
            return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
        return send_file(abs_path, as_attachment=not preview)
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500




# ═══════════════════════════════════════════════════════════════
# IA CASCADE ENDPOINTS v3.0
# ═══════════════════════════════════════════════════════════════

def _ia_cascade_unavailable_response():
    return jsonify({
        'success': False,
        'error': 'IA Cascade no disponible'
    }), 503


def _ensure_ia_cascade_audit_table():
    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS ia_cascade_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                request_id TEXT,
                correlation_id TEXT,
                endpoint TEXT,
                user_id TEXT,
                forced_provider TEXT,
                provider_used TEXT,
                success INTEGER,
                elapsed_ms REAL,
                prompt_hash TEXT,
                prompt_preview TEXT,
                error TEXT,
                metadata_json TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def _log_ia_cascade_audit(
    endpoint,
    user_id,
    prompt,
    forced_provider,
    result,
    request_id,
    correlation_id,
):
    _ensure_ia_cascade_audit_table()
    prompt_text = (prompt or "").strip()
    prompt_hash = hashlib.sha256(prompt_text.encode("utf-8")).hexdigest() if prompt_text else ""
    preview = prompt_text[:160]
    metadata = result.get("metadata", {}) if isinstance(result, dict) else {}
    provider_used = result.get("provider_used") if isinstance(result, dict) else None
    success = 1 if (isinstance(result, dict) and result.get("success")) else 0
    elapsed_ms = float(result.get("time", 0) or 0) * 1000 if isinstance(result, dict) else 0
    error = result.get("error") if isinstance(result, dict) else "resultado inválido"

    conn = db.get_connection()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO ia_cascade_audit
            (
                request_id, correlation_id, endpoint, user_id, forced_provider, provider_used,
                success, elapsed_ms, prompt_hash, prompt_preview, error, metadata_json
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                request_id,
                correlation_id,
                endpoint,
                str(user_id) if user_id is not None else None,
                forced_provider,
                provider_used,
                success,
                elapsed_ms,
                prompt_hash,
                preview,
                error,
                json.dumps(metadata, ensure_ascii=False),
            ),
        )
        conn.commit()
    finally:
        conn.close()

@app.route('/api/ia-cascade/stats', methods=['GET'])
@jwt_required()
def ia_cascade_stats():
    """
    Obtener estadísticas de todos los providers
    
    Returns:
        JSON con stats globales y por provider
    """
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        stats = ia_cascade.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/ia-cascade/stats-public', methods=['GET'])
@jwt_required_custom
def ia_cascade_stats_public():
    """Endpoint protegido (compat legacy) para IA Cascade stats"""
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        stats = ia_cascade.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_stats_public: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/providers-public', methods=['GET'])
@jwt_required_custom
def ia_cascade_providers_public():
    """Endpoint protegido (compat legacy) para providers config"""
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        providers = ia_cascade.get_all_providers_config()
        return jsonify({
            'success': True,
            'providers': providers
        }), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_providers_public: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/providers', methods=['GET'])
@jwt_required()
def ia_cascade_providers():
    """
    Obtener configuración de todos los providers (sin API keys)
    
    Returns:
        JSON con nombre, modelo, estado, prioridad de cada provider
    """
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        providers = ia_cascade.get_all_providers_config()
        return jsonify({
            'success': True,
            'providers': providers
        }), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_providers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/test', methods=['POST'])
@jwt_required()
def ia_cascade_test():
    """
    Testar un provider específico o cascade automático
    
    Body JSON:
        - prompt: str (requerido)
        - provider: str (opcional, default 'cascade')
        - temperature: float (opcional, default 0.3)
        - max_tokens: int (opcional, default 2000)
    
    Returns:
        JSON con respuesta, provider usado, tiempo, metadata
    """
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        data = request.json
        prompt = data.get('prompt', '¿Qué es el artículo 133 de la LEC?')
        provider = data.get('provider', 'cascade')
        temperature = data.get('temperature', 0.3)
        max_tokens = data.get('max_tokens', 2000)
        user_id = get_jwt_identity()
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        correlation_id = request.headers.get("X-Correlation-ID") or request_id
        
        print(f"🧪 Test IA Cascade: provider={provider}, temp={temperature}")
        
        if provider == 'cascade':
            result = ia_cascade.consultar_cascade(prompt, temperature, max_tokens)
        else:
            result = ia_cascade.consultar_cascade(prompt, temperature, max_tokens, force_provider=provider)

        _log_ia_cascade_audit(
            endpoint="/api/ia-cascade/test",
            user_id=user_id,
            prompt=prompt,
            forced_provider=None if provider == "cascade" else provider,
            result=result,
            request_id=request_id,
            correlation_id=correlation_id,
        )
        
        return jsonify({
            'success': result.get('success'),
            'response': result.get('response'),
            'provider_used': result.get('provider_used'),
            'time': result.get('time'),
            'metadata': result.get('metadata', {}),
            'request_id': request_id,
            'correlation_id': correlation_id,
            'error': result.get('error')
        }), 200
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_test: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/update-key', methods=['POST'])
@jwt_required()
def ia_cascade_update_key():
    """
    Actualizar API key de un provider
    
    Body JSON:
        - provider_id: str (requerido)
        - api_key: str (requerido)
    """
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        data = request.json
        provider_id = data.get('provider_id')
        api_key = data.get('api_key')
        
        if not provider_id or not api_key:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros: provider_id y api_key son requeridos'
            }), 400
        
        success = ia_cascade.update_api_key(provider_id, api_key)
        
        if success:
            print(f"✅ API key de {provider_id} actualizada")
            return jsonify({
                'success': True,
                'message': f'✅ API key de {provider_id} actualizada correctamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_id} no encontrado'
            }), 404
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_update_key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/toggle-provider', methods=['POST'])
@jwt_required()
def ia_cascade_toggle_provider():
    """
    Habilitar/deshabilitar un provider
    
    Body JSON:
        - provider_id: str (requerido)
        - enabled: bool (requerido)
    """
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        data = request.json
        provider_id = data.get('provider_id')
        enabled = data.get('enabled', False)
        
        if not provider_id:
            return jsonify({
                'success': False,
                'error': 'Falta parámetro: provider_id es requerido'
            }), 400
        
        success = ia_cascade.toggle_provider(provider_id, enabled)
        
        if success:
            status = '✅ habilitado' if enabled else '⏸️ deshabilitado'
            print(f"{status}: {provider_id}")
            return jsonify({
                'success': True,
                'message': f'Provider {provider_id} {status}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_id} no encontrado'
            }), 404
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_toggle_provider: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/reset-stats', methods=['POST'])
@jwt_required()
def ia_cascade_reset_stats():
    """
    Resetear estadísticas de un provider o todos
    
    Body JSON (opcional):
        - provider_id: str (opcional, si se omite resetea todos)
    """
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        data = request.json or {}
        provider_id = data.get('provider_id')
        
        ia_cascade.reset_stats(provider_id)
        
        if provider_id:
            print(f"🗑️ Stats reseteadas para {provider_id}")
            message = f'Stats reseteadas para {provider_id}'
        else:
            print(f"🗑️ Stats reseteadas globalmente")
            message = 'Stats reseteadas globalmente'
        
        return jsonify({
            'success': True,
            'message': message,
            'stats': ia_cascade.get_stats()
        }), 200
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_reset_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ia-cascade/health', methods=['GET'])
def ia_cascade_health():
    """Estado operativo de IA Cascade (enterprise healthcheck)."""
    try:
        if ia_cascade is None:
            return _ia_cascade_unavailable_response()
        return jsonify(ia_cascade.health_check()), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_health: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# AUTO-PROCESSOR ENDPOINTS (HEREDADOS - MANTENER)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/dashboard/drill-down/by-date/<date_str>', methods=['GET'])
@jwt_required_custom
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
@jwt_required()
def export_dashboard_pdf():
    """
    Exportar estadísticas del dashboard a PDF (v2.2.0)
    """
    try:
        # 1. Obtener datos detallados (reusa endpoint)
        stats_response = dashboard_stats_detailed()
        if not hasattr(stats_response, "get_json"):
            return stats_response
        if stats_response.status_code != 200:
            return stats_response
        payload = stats_response.get_json() or {}
        stats_data = payload.get('stats', {})
        trends = payload.get('trends', {})
        kpis = payload.get('kpis', {})
        recent_docs = payload.get('recent_docs', [])
        recent_alerts = payload.get('recent_alerts', [])
        
        # 2. Generar PDF sencillo (ReportLab si disponible; fallback manual si no)
        try:
            from reportlab.pdfgen import canvas
            from reportlab.lib.pagesizes import A4
            pdf_buffer = io.BytesIO()
            c = canvas.Canvas(pdf_buffer, pagesize=A4)
            width, height = A4
            y = height - 50
            c.setFont("Helvetica-Bold", 14)
            c.drawString(40, y, "Reporte Dashboard LexDocsPro")
            y -= 24
            c.setFont("Helvetica", 10)
            c.drawString(40, y, f"Generado por: {get_jwt_identity() or 'usuario'}")
            y -= 18
            c.drawString(40, y, f"Total documentos: {stats_data.get('total_documents', 0)}")
            y -= 14
            c.drawString(40, y, f"Hoy: {kpis.get('today', 0)}  Semana: {kpis.get('week', 0)}  Mes: {kpis.get('month', 0)}")
            y -= 22
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Top tipos (30 días)")
            y -= 16
            c.setFont("Helvetica", 10)
            for t, v in (stats_data.get('by_type') or {}).items():
                c.drawString(50, y, f"- {t}: {v}")
                y -= 14
                if y < 80:
                    c.showPage(); y = height - 50
            y -= 6
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Últimos documentos")
            y -= 16
            c.setFont("Helvetica", 10)
            for doc in recent_docs:
                c.drawString(50, y, f"- {doc.get('name','')} ({doc.get('time','')})")
                y -= 14
                if y < 80:
                    c.showPage(); y = height - 50
            y -= 6
            c.setFont("Helvetica-Bold", 12)
            c.drawString(40, y, "Alertas recientes")
            y -= 16
            c.setFont("Helvetica", 10)
            for al in recent_alerts:
                c.drawString(50, y, f"- [{al.get('urgency','')}] {al.get('title','')} ({al.get('time','')})")
                y -= 14
                if y < 80:
                    c.showPage(); y = height - 50
            c.showPage()
            c.save()
            pdf_buffer.seek(0)
        except Exception as e:
            print(f"❌ Error generando PDF con reportlab: {e}")
            # Fallback mínimo PDF sin dependencias
            def simple_pdf(text_lines):
                buf = io.BytesIO()
                # muy simple PDF 1.1
                lines = text_lines or ["Reporte Dashboard"]
                text = "\\n".join(lines)
                content = f"BT /F1 12 Tf 50 750 Td ({text}) Tj ET"
                pdf = f"%PDF-1.1\\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\\n2 0 obj<</Type/Pages/Count 1/Kids[3 0 R]>>endobj\\n3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 612 792]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\\n4 0 obj<</Length {len(content)}>>stream\\n{content}\\nendstream endobj\\n5 0 obj<</Type/Font/Subtype/Type1/Name/F1/BaseFont/Helvetica>>endobj\\nxref\\n0 6\\n0000000000 65535 f \\n0000000010 00000 n \\n0000000060 00000 n \\n0000000114 00000 n \\n0000000277 00000 n \\n0000000420 00000 n \\ntrailer<</Size 6/Root 1 0 R>>\\nstartxref\\n518\\n%%EOF"
                buf.write(pdf.encode("latin-1"))
                buf.seek(0)
                return buf
            lines = [
                "Reporte Dashboard LexDocsPro",
                f"Total documentos: {stats_data.get('total_documents',0)}",
                f"Hoy: {kpis.get('today',0)}  Semana: {kpis.get('week',0)}  Mes: {kpis.get('month',0)}",
                "Top tipos:",
            ]
            for t,v in (stats_data.get('by_type') or {}).items():
                lines.append(f" - {t}: {v}")
            lines.append("Últimos documentos:")
            for d in recent_docs[:10]:
                lines.append(f" - {d.get('name','')} {d.get('time','')}")
            lines.append("Alertas recientes:")
            for a in recent_alerts[:10]:
                lines.append(f" - [{a.get('urgency','')}] {a.get('title','')} {a.get('time','')}")
            pdf_buffer = simple_pdf(lines)
        
        # 3. Responder
        user_id = get_jwt_identity()
        user = db.get_user_by_id(user_id)
        user_name = user.get('nombre', 'Admin') if user else 'Admin'
        return send_file(pdf_buffer, mimetype='application/pdf', as_attachment=True,
                         download_name=f"reporte_dashboard_{datetime.now().strftime('%Y%m%d')}.pdf")
        
    except Exception as e:
        print(f"❌ Error exportando PDF: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# AI AGENT FEEDBACK LOOP (v3.0.0)
# ============================================

@app.route('/api/agent/feedback', methods=['POST'])
@abogado_or_admin_required
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
@abogado_or_admin_required
def list_certificates():
    """Listar certificados disponibles para firmar"""
    try:
        certs = signature_service.list_available_certificates()
        return jsonify({'success': True, 'certificates': certs, 'path': signature_service.certificates_path})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/signature/sign', methods=['POST'])
@abogado_or_admin_required
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
        data = request.get_json(silent=True) or {}
        doc_id = data.get('doc_id')
        cert_name = (data.get('certificate') or '').strip()
        passphrase = (data.get('passphrase') or '').strip()
        
        if not doc_id or not cert_name:
            return jsonify({'success': False, 'error': 'Faltan doc_id y certificate'}), 400

        documento = None
        doc_path = None
        try:
            doc_int = int(doc_id)
            documento = db.get_saved_document(doc_int) if 'db' in globals() and db else None
        except (TypeError, ValueError):
            documento = None

        doc_input = str(doc_id).strip().strip('"').strip("'")
        if doc_input.startswith("~"):
            doc_input = os.path.expanduser(doc_input)

        if documento:
            doc_path = documento.get('file_path')
        elif os.path.exists(doc_input):
            doc_path = doc_input
        else:
            # Búsqueda por nombre en roots OCR
            found = find_file_in_roots(doc_input)
            if found:
                doc_path = found

        if not doc_path or not os.path.exists(doc_path):
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404

        available = {c.get('name') for c in signature_service.list_available_certificates() if c.get('name')}
        if cert_name not in available:
            return jsonify({
                'success': False,
                'error': 'Certificado no disponible',
                'available_certificates': sorted(available)
            }), 400

        input_path = doc_path
        base_name = os.path.basename(input_path)
        output_filename = f"FIRMADO_{base_name}"
        output_path = os.path.join(os.path.dirname(input_path), output_filename)
        
        success, err = signature_service.sign_pdf(input_path, output_path, cert_name, passphrase)
        
        if success:
            # Registrar en log y opcionalmente actualizar el documento en BD
            db.registrar_log('info', 'signature', f"Documento {doc_id} firmado con {cert_name}")
            return jsonify({
                'success': True, 
                'mensaje': 'Documento firmado con éxito',
                'signed_path': output_path
            })
        else:
            return jsonify({
                'success': False,
                'error': err or 'No se pudo firmar el documento con los parámetros actuales'
            }), 422
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# SERVIR FRONTEND VANILLA JS (v2.3.1)
# ============================================

@app.route('/')
def index():
    """Servir la UI principal Vanilla JS"""
    return render_template('index.html')

@app.route('/<path:path>')
def serve_static(path):
    """Servir archivos estáticos desde /static"""
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    return jsonify({'error': 'Not Found'}), 404

# ============================================
# HEALTH CHECK
# ============================================

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'success': True,
        'service': 'lexdocspro-lite',
        'status': 'ok'
    }), 200

@app.route('/api/status/overview', methods=['GET'])
def status_overview():
    """Estado rápido de servicios críticos para la banda de salud UI."""
    try:
        # IA local
        ia_local = ai_service.providers.get('ollama').is_available() if ai_service and ai_service.providers.get('ollama') else False
        # SMTP configurado
        smtp_ready = all(os.getenv(k) for k in ('SMTP_HOST', 'SMTP_USER', 'SMTP_PASS'))
        # LexNET: considera configurado si tabla notifications existe y LexNetNotifications inicializa
        try:
            from services.lexnet_notifications import LexNetNotifications
            lexnet_ok = True
            LexNetNotifications(db_manager=db)  # ensure schema
        except Exception:
            lexnet_ok = False
        # Autoprocesador
        auto_running = autoprocessor.get_status().get('running', False)

        return jsonify({
            'success': True,
            'services': {
                'ia_local': ia_local,
                'smtp': smtp_ready,
                'lexnet': lexnet_ok,
                'autoprocesor': auto_running
            }
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============================================
# NEW FEATURE ENDPOINTS (v2.3.1 CLASSIC)
# ============================================

@app.route('/api/banking/stats', methods=['GET'])
@abogado_or_admin_required
def get_banking_stats():
    """Obtener resumen de conciliación bancaria (proveedor real si está configurado)."""
    try:
        from services.banking_service import BankingService
        service = BankingService()
        result = service.get_stats()
        if result.get('success'):
            return jsonify({'success': True, 'stats': result.get('stats', {}), 'configured': True}), 200
        return jsonify({
            'success': False,
            'configured': False,
            'error': result.get('error', 'Banking no configurado'),
            'stats': result.get('stats', {
                'bancos_activos': 0,
                'pendientes_conciliar': 0,
                'ultimo_sincro': None,
                'alerts_criticas': 0,
            })
        }), 200
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
@abogado_or_admin_required
def test_email_alert():
    """Enviar un email de prueba (Email Alerts feature)"""
    try:
        from services.email_service import EmailService
        email_service = EmailService()
        data = request.get_json(silent=True) or {}
        to_email = data.get('to_email') or data.get('email')
        ok, err = email_service._validate_config()
        if not ok:
            return jsonify({'success': False, 'configured': False, 'error': err}), 400
        # Enviar email al usuario logueado
        success = email_service.send_alert(
            subject="LexDocsPro LITE: Test de Alerta Crítica",
            body="Este es un test de la funcionalidad Email Alerts v2.3.1.",
            to_email=to_email
        )
        return jsonify({'success': success, 'configured': success}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/alerts/status', methods=['GET'])
@abogado_or_admin_required
def alerts_status():
    """Estado de configuración SMTP para Alertas."""
    from services.email_service import EmailService
    svc = EmailService()
    ok, err = svc._validate_config()
    return jsonify({
        'success': True,
        'smtp_configured': ok,
        'error': None if ok else err,
        'from': svc.smtp_from,
        'default_to': svc.default_to
    }), 200

# ============================================
# LEGACY COMPAT ENDPOINTS (P0 CONTRATO)
# ============================================

LEGACY_CONFIG = {
    'alert_email': 'admin@lexdocs.com',
    'ia_fallback': True,
    'ollama_model': OLLAMA_MODEL,
    'pendientes_dir': PENDIENTES_DIR,
}

@app.route('/api/watchdog-status', methods=['GET'])
def legacy_watchdog_status():
    status = autoprocessor.get_status()
    return jsonify({
        'success': True,
        'status': 'running' if status.get('running') else 'stopped',
        'watchdog': status,
        'kpis': {
            'running': bool(status.get('running')),
            'queued_files': status.get('queued_files', 0),
            'processed_today': status.get('processed_today', 0)
        },
        'trends': {
            'labels': ['h-3', 'h-2', 'h-1', 'now'],
            'values': [0, 0, 0, status.get('processed_today', 0)]
        }
    }), 200

@app.route('/api/autoprocesos/logs', methods=['GET'])
def legacy_autoprocesos_logs():
    log = autoprocessor.get_processing_log(limit=30)
    lines = []
    for item in log:
        lines.append(
            f"{item.get('completed_at', '')} | {item.get('status', '')} | {item.get('filename', '')}"
        )
    return jsonify({'success': True, 'status': 'ok', 'logs': lines}), 200

@app.route('/api/autoprocesos/toggle', methods=['POST'])
def legacy_autoprocesos_toggle():
    data = request.get_json(silent=True) or {}
    action = data.get('action', 'status')
    if action == 'start':
        autoprocessor.start()
    elif action == 'stop':
        autoprocessor.stop()
    status = autoprocessor.get_status()
    return jsonify({
        'success': True,
        'status': 'running' if status.get('running') else 'stopped'
    }), 200

@app.route('/api/ia-cascade/status', methods=['GET'])
def legacy_ia_cascade_status():
    if ia_cascade is None:
        return jsonify({'success': False, 'error': 'IA Cascade no disponible'}), 503
    stats = ia_cascade.get_stats()
    providers_cfg = ia_cascade.get_all_providers_config()
    providers = []
    for provider_id, cfg in providers_cfg.items():
        pstats = stats.get('providers', {}).get(provider_id, {})
        providers.append({
            'id': provider_id,
            'name': cfg.get('name'),
            'model': cfg.get('model'),
            'available': cfg.get('enabled', False),
            'priority': cfg.get('priority', 99),
            'stats': {
                'requests': pstats.get('total_calls', 0),
                'success': pstats.get('successful_calls', 0),
                'failed': pstats.get('failed_calls', 0),
            }
        })
    return jsonify({
        'success': True,
        'status': {
            'global_stats': {
                'total_requests': stats.get('global', {}).get('total_calls', 0),
                'successful': stats.get('global', {}).get('successful_calls', 0),
                'failed': stats.get('global', {}).get('failed_calls', 0),
            },
            'providers': providers
        }
    }), 200

@app.route('/api/ai/models', methods=['GET'])
@abogado_or_admin_required
def list_ai_models():
    """Listar modelos disponibles en Ollama y el modelo actual."""
    result = ai_service.get_ollama_models()
    status_code = 200 if result.get('success') else 503
    return jsonify(result), status_code

@app.route('/api/ai/models', methods=['POST'])
@abogado_or_admin_required
def set_ai_model():
    """Seleccionar el modelo Ollama activo."""
    data = request.get_json(silent=True) or {}
    model = data.get('model')
    result = ai_service.set_ollama_model(model)
    status_code = 200 if result.get('success') else 400
    return jsonify(result), status_code

@app.route('/api/ia-cascade/query', methods=['POST'])
def legacy_ia_cascade_query():
    if ia_cascade is None:
        return jsonify({'success': False, 'error': 'IA Cascade no disponible'}), 503
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '')
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    correlation_id = request.headers.get("X-Correlation-ID") or request_id
    result = ia_cascade.consultar_cascade(prompt, temperature=0.3, max_tokens=1500)
    _log_ia_cascade_audit(
        endpoint="/api/ia-cascade/query",
        user_id=None,
        prompt=prompt,
        forced_provider=None,
        result=result,
        request_id=request_id,
        correlation_id=correlation_id,
    )
    return jsonify({
        'success': result.get('success', False),
        'provider': result.get('provider_used'),
        'model': result.get('metadata', {}).get('model'),
        'response': result.get('response', ''),
        'request_id': request_id,
        'correlation_id': correlation_id,
        'error': result.get('error')
    }), 200

@app.route('/api/ia/consultar', methods=['POST'])
def legacy_ia_consultar():
    data = request.get_json(silent=True) or {}
    prompt = data.get('prompt', '')
    provider = data.get('provider', 'ollama')
    respuesta = ai_service.consultar('', prompt, provider=provider, mode='standard')
    return jsonify({
        'success': True,
        'provider': provider,
        'respuesta': respuesta
    }), 200

@app.route('/api/ia/agent-task', methods=['POST'])
def legacy_ia_agent_task():
    data = request.get_json(silent=True) or {}
    task = data.get('task', 'Sin tarea')
    steps = [
        'Analizando contexto',
        'Buscando datos relevantes',
        'Proponiendo acción',
        'Generando resultado'
    ]
    result = f"Tarea procesada: {task}"
    return jsonify({
        'success': True,
        'steps': steps,
        'result': result,
        'performance': {
            'duration_ms': 120,
            'tokens_estimated': max(32, len(task.split()) * 8)
        }
    }), 200

@app.route('/api/pdf/preview-data', methods=['GET'])
def legacy_pdf_preview_data():
    thumbs = [
        {'page': 1, 'url': ''},
        {'page': 2, 'url': ''},
    ]
    return jsonify({
        'success': True,
        'filename': 'expediente_demo.pdf',
        'thumbnails': thumbs
    }), 200

@app.route('/api/alerts/config', methods=['POST'])
def legacy_alerts_config():
    data = request.get_json(silent=True) or {}
    email = data.get('email')
    if not email:
        return jsonify({'success': False, 'error': 'email requerido'}), 400
    LEGACY_CONFIG['alert_email'] = email
    history = [
        {'tipo': 'INFO', 'asunto': 'Configuración de alertas actualizada', 'fecha': datetime.now().strftime("%d/%m/%Y %H:%M"), 'estado': 'Enviado'}
    ]
    return jsonify({
        'success': True,
        'message': f'Email guardado: {email}',
        'history': history
    }), 200

@app.route('/api/alerts/history', methods=['GET'])
def legacy_alerts_history():
    history = [
        {'tipo': 'CRÍTICA', 'asunto': 'Plazo próximo a vencer', 'fecha': datetime.now().strftime("%d/%m/%Y %H:%M"), 'estado': 'Enviado'},
        {'tipo': 'INFO', 'asunto': 'Sincronización completada', 'fecha': datetime.now().strftime("%d/%m/%Y %H:%M"), 'estado': 'Enviado'},
    ]
    return jsonify({'success': True, 'history': history}), 200

@app.route('/api/firma/status', methods=['GET'])
def legacy_firma_status():
    certs = signature_service.list_available_certificates()
    return jsonify({
        'success': True,
        'certificates': certs,
        'certificates_path': signature_service.certificates_path,
        'message': 'Estado de firma cargado',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/firma/ejecutar', methods=['POST'])
def legacy_firma_ejecutar():
    data = request.get_json(silent=True) or {}
    doc_id = data.get('doc_id', 'N/A')
    return jsonify({
        'success': True,
        'message': f'Documento firmado (simulado): {doc_id}',
        'hash': 'SIMULATED-HASH',
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/banking/institutions', methods=['GET'])
def legacy_banking_institutions():
    try:
        from services.banking_service import BankingService
        service = BankingService()
        country = request.args.get('country', None)
        result = service.get_institutions(country=country)
        if result.get('success'):
            return jsonify({'success': True, 'configured': True, 'banks': result.get('institutions', [])}), 200
        return jsonify({
            'success': False,
            'configured': False,
            'error': result.get('error', 'Banking no configurado'),
            'banks': []
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'banks': []}), 500

@app.route('/api/banking/transactions', methods=['GET'])
def legacy_banking_transactions():
    try:
        from services.banking_service import BankingService
        service = BankingService()
        limit = request.args.get('limit', 50, type=int)
        result = service.get_transactions(limit=limit)
        if result.get('success'):
            return jsonify({'success': True, 'configured': True, 'transactions': result.get('transactions', [])}), 200
        return jsonify({
            'success': False,
            'configured': False,
            'error': result.get('error', 'Banking no configurado'),
            'transactions': []
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'transactions': []}), 500

@app.route('/api/usuarios/equipo', methods=['GET'])
@abogado_or_admin_required
def legacy_usuarios_equipo():
    try:
        from services.auth_service import AuthDB
        adb = AuthDB()
        rows = adb.list_users()
        usuarios = []
        for u in rows:
            usuarios.append({
                'id': u.get('id'),
                'nombre': u.get('nombre') or u.get('email'),
                'email': u.get('email'),
                'rol': u.get('rol', 'LECTURA'),
                'status': 'Online' if u.get('activo') else 'Inactivo',
                'actividad': u.get('last_login') or u.get('created_at') or ''
            })
        return jsonify({'success': True, 'usuarios': usuarios, 'total': len(usuarios)}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'usuarios': []}), 500

@app.route('/api/usuarios/registrar', methods=['POST'])
@admin_required
def legacy_usuarios_registrar():
    data = request.get_json(silent=True) or {}
    nombre = (data.get('nombre') or '').strip()
    email = (data.get('email') or '').strip().lower()
    rol = (data.get('rol') or 'LECTURA').strip().upper()
    password = (data.get('password') or '').strip()

    if not email:
        return jsonify({'success': False, 'message': 'email requerido'}), 400
    if rol not in {'ADMIN', 'ABOGADO', 'LECTURA'}:
        return jsonify({'success': False, 'message': 'rol inválido'}), 400

    if not password:
        alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
        password = ''.join(secrets.choice(alphabet) for _ in range(12))

    try:
        from services.auth_service import AuthDB, AuthService
        adb = AuthDB()
        asvc = AuthService(adb)
        result = asvc.register_user(email=email, password=password, rol=rol, nombre=nombre or None)
        if not result.get('success'):
            return jsonify({'success': False, 'message': result.get('error', 'No se pudo registrar')}), 400
        return jsonify({
            'success': True,
            'message': f'Usuario creado: {email}',
            'user_id': result.get('user_id'),
            'rol': rol,
            'temporary_password': password
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/usuarios/<int:user_id>/estado', methods=['POST'])
@admin_required
def legacy_usuarios_estado(user_id):
    current_user_id = get_jwt_identity()
    if int(current_user_id) == int(user_id):
        return jsonify({'success': False, 'error': 'No puedes desactivarte a ti mismo'}), 400

    data = request.get_json(silent=True) or {}
    activo = bool(data.get('activo', True))
    try:
        from services.auth_service import AuthDB
        adb = AuthDB()
        if activo:
            conn = adb._connect()
            cur = conn.cursor()
            cur.execute("UPDATE users SET activo = 1 WHERE id = ?", (user_id,))
            conn.commit()
            conn.close()
        else:
            adb.deactivate_user(user_id)
        return jsonify({'success': True, 'user_id': user_id, 'activo': activo}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/usuarios/<int:user_id>/reset-password', methods=['POST'])
@admin_required
def legacy_usuarios_reset_password(user_id):
    current_user_id = get_jwt_identity()
    if int(current_user_id) == int(user_id):
        return jsonify({'success': False, 'error': 'No puedes resetear tu propia contraseña desde este endpoint'}), 400

    alphabet = 'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnpqrstuvwxyz23456789'
    temp_password = ''.join(secrets.choice(alphabet) for _ in range(12))

    try:
        from werkzeug.security import generate_password_hash
        from services.auth_service import AuthDB
        adb = AuthDB()
        conn = adb._connect()
        cur = conn.cursor()
        cur.execute("UPDATE users SET password_hash = ? WHERE id = ?", (generate_password_hash(temp_password), user_id))
        changed = cur.rowcount
        conn.commit()
        conn.close()
        if not changed:
            return jsonify({'success': False, 'error': 'Usuario no encontrado'}), 404
        try:
            adb.log_action(int(current_user_id), f'RESET_PASSWORD_USER_{user_id}', request.remote_addr)
        except Exception:
            pass
        return jsonify({'success': True, 'user_id': user_id, 'temporary_password': temp_password}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/analytics/detailed', methods=['GET'])
def legacy_analytics_detailed():
    return jsonify({
        'success': True,
        'performance': {
            'win_rate': 87,
            'ahorro_horas_mes': 34
        },
        'expedientes_por_tipo': {
            'labels': ['Civil', 'Penal', 'Laboral', 'Mercantil'],
            'values': [42, 25, 18, 15]
        },
        'roi_data': {
            'labels': ['Ene', 'Feb', 'Mar', 'Abr'],
            'ahorro_euro': [1200, 1800, 2200, 2600]
        }
    }), 200

@app.route('/api/expedientes/listar', methods=['GET'])
def legacy_expedientes_listar():
    requested_path = (request.args.get('path') or '').strip()

    roots = []
    for raw in [
        EXPEDIENTES_DIR,
        os.path.expanduser('~/Library/Mobile Documents/com~apple~CloudDocs/EXPEDIENTES'),
        BASE_DIR,
    ]:
        p = Path(raw).expanduser().resolve()
        if p.exists() and p.is_dir() and str(p) not in [str(x) for x in roots]:
            roots.append(p)

    if not roots:
        return jsonify({'success': False, 'error': 'No hay raíces de expedientes disponibles'}), 500

    if requested_path:
        current = Path(requested_path).expanduser().resolve()
    else:
        current = roots[0]

    if not any(current == r or r in current.parents for r in roots):
        return jsonify({
            'success': False,
            'error': 'Ruta fuera de raíces permitidas',
            'current_path': str(roots[0]),
            'roots': [str(r) for r in roots]
        }), 400

    files = []
    if current.exists() and current.is_dir():
        entries = sorted(
            list(current.iterdir()),
            key=lambda x: (not x.is_dir(), x.name.lower())
        )
        for item in entries[:200]:
            try:
                stat = item.stat()
                files.append({
                    'name': item.name,
                    'path': str(item.resolve()),
                    'is_dir': item.is_dir(),
                    'size': stat.st_size if item.is_file() else None,
                    'mtime': datetime.fromtimestamp(stat.st_mtime).strftime('%d/%m/%Y %H:%M')
                })
            except Exception:
                continue

    parent_path = None
    if current.parent != current and any(current.parent == r or r in current.parent.parents for r in roots):
        parent_path = str(current.parent)

    return jsonify({
        'success': True,
        'current_path': str(current),
        'parent_path': parent_path,
        'roots': [str(r) for r in roots],
        'files': files
    }), 200

@app.route('/api/lexnet-urgent', methods=['GET'])
def legacy_lexnet_urgent():
    try:
        urgent_count = 0
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM notifications WHERE urgency IN ('CRITICAL','URGENT') AND read = 0")
        urgent_count = cursor.fetchone()[0] or 0
        conn.close()
    except Exception:
        urgent_count = 0
    return jsonify({'success': True, 'count': urgent_count}), 200

@app.route('/api/lexnet/analizar-plazo', methods=['POST'])
def legacy_lexnet_analizar_plazo():
    data = request.get_json(silent=True) or {}
    dias = int(data.get('dias', 20))
    fecha_notificacion = datetime.now().strftime('%Y-%m-%d')
    try:
        fecha_limite = lexnet_analyzer.calcular_plazo(fecha_notificacion, dias)
    except Exception:
        fecha_limite = datetime.now().strftime('%d/%m/%Y')
    return jsonify({
        'success': True,
        'fecha_notificacion': datetime.now().strftime('%d/%m/%Y'),
        'dias_habiles': dias,
        'fecha_limite': fecha_limite,
        'config': {
            'territorio': 'Canarias',
            'festivos_base': 2026
        }
    }), 200

@app.route('/api/config/get', methods=['GET'])
def legacy_config_get():
    # Estado rápido de servicios para panel de configuración
    smtp_ok = False
    smtp_error = None
    try:
        from services.email_service import EmailService
        _ok, _err = EmailService()._validate_config()
        smtp_ok = bool(_ok)
        smtp_error = None if _ok else _err
    except Exception as e:
        smtp_error = str(e)

    ia_ok = False
    try:
        ia_ok = ia_cascade is not None and bool(getattr(ia_cascade, "providers", {}))
    except Exception:
        ia_ok = False

    lexnet_ok = False
    try:
        from services.lexnet_notifications import LexNetNotifications
        LexNetNotifications(db_manager=db)
        lexnet_ok = True
    except Exception:
        lexnet_ok = False

    watchdog_status = {}
    try:
        watchdog_status = autoprocessor.get_status() or {}
    except Exception:
        watchdog_status = {}

    return jsonify({
        'success': True,
        'message': 'Configuración cargada',
        'config': {
            'alert_email': LEGACY_CONFIG.get('alert_email', 'admin@lexdocs.com'),
            'ollama_model': LEGACY_CONFIG.get('ollama_model', OLLAMA_MODEL),
            'pendientes_dir': LEGACY_CONFIG.get('pendientes_dir', PENDIENTES_DIR),
            'ia_fallback': LEGACY_CONFIG.get('ia_fallback', True),
            'default_ai_provider': LEGACY_CONFIG.get('default_ai_provider', DEFAULT_AI_PROVIDER),
        },
        'services': {
            'ia_cascade': {'ok': ia_ok},
            'smtp': {'ok': smtp_ok, 'error': smtp_error},
            'lexnet': {'ok': lexnet_ok},
            'watchdog': {
                'ok': bool(watchdog_status.get('running')),
                'running': bool(watchdog_status.get('running')),
                'queued_files': int(watchdog_status.get('queued_files', 0)),
                'processed_today': int(watchdog_status.get('processed_today', 0)),
            }
        },
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/config/save', methods=['POST'])
def legacy_config_save():
    data = request.get_json(silent=True) or {}
    updated = {}

    alert_email = (data.get('alert_email') or '').strip()
    if alert_email:
        LEGACY_CONFIG['alert_email'] = alert_email
        updated['alert_email'] = alert_email

    if 'ollama_model' in data:
        value = str(data['ollama_model']).strip()
        if value:
            LEGACY_CONFIG['ollama_model'] = value
            updated['ollama_model'] = value

    if 'pendientes_dir' in data:
        value = str(data['pendientes_dir']).strip()
        if value:
            LEGACY_CONFIG['pendientes_dir'] = value
            updated['pendientes_dir'] = value

    if 'ia_fallback' in data:
        value = bool(data['ia_fallback'])
        LEGACY_CONFIG['ia_fallback'] = value
        updated['ia_fallback'] = value

    if 'default_ai_provider' in data:
        value = str(data['default_ai_provider']).strip().lower()
        if value:
            LEGACY_CONFIG['default_ai_provider'] = value
            updated['default_ai_provider'] = value

    if not updated:
        return jsonify({
            'success': False,
            'message': 'No hay campos válidos para guardar'
        }), 400

    return jsonify({
        'success': True,
        'message': 'Configuración guardada',
        'updated': updated,
        'services': {
            'autoprocesador': 'online',
            'ia_cascade': 'online',
            'storage': 'online'
        },
        'timestamp': datetime.now().isoformat()
    }), 200

@app.route('/api/deploy/status', methods=['GET'])
def legacy_deploy_status():
    # Estado real y compatible con la respuesta legacy.
    import socket
    from config import DB_PATH

    def _status_label(ok):
        return 'Online' if ok else 'Degraded'

    # Database
    db_ok = False
    db_error = None
    try:
        conn = db.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1")
        cur.fetchone()
        conn.close()
        db_ok = True
    except Exception as e:
        db_error = str(e)

    # Ollama
    ollama_ok = False
    ollama_error = None
    ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434').rstrip('/')
    try:
        resp = requests.get(f"{ollama_url}/api/tags", timeout=2)
        ollama_ok = resp.status_code < 500
        if not ollama_ok:
            ollama_error = f"HTTP {resp.status_code}"
    except Exception as e:
        ollama_error = str(e)

    # Storage
    storage_ok = True
    storage_error = None
    ap_status = {}
    try:
        ap_status = autoprocessor.get_status() or {}
    except Exception:
        ap_status = {}
    storage_paths = [
        PENDIENTES_DIR,
        ap_status.get('processed_dir') or os.path.expanduser('~/Desktop/PROCESADOS_LEXDOCS'),
        ap_status.get('error_dir') or os.path.expanduser('~/Desktop/ERRORES_LEXDOCS'),
        ap_status.get('backup_dir') or os.path.expanduser('~/Desktop/BACKUP_LEXDOCS'),
        GENERATED_DOCS_DIR,
    ]
    for p in storage_paths:
        try:
            os.makedirs(p, exist_ok=True)
            probe = os.path.join(p, '.lexdocs_probe')
            with open(probe, 'w', encoding='utf-8') as f:
                f.write('ok')
            os.remove(probe)
        except Exception as e:
            storage_ok = False
            storage_error = f"{p}: {e}"
            break

    # PWA assets mínimos
    pwa_ok = True
    pwa_error = None
    project_root = os.path.dirname(os.path.abspath(__file__))
    required_assets = ['templates/index.html', 'static/css/style.css']
    for asset in required_assets:
        if not os.path.exists(os.path.join(project_root, asset)):
            pwa_ok = False
            pwa_error = f"Falta {asset}"
            break

    # Watchdog/autoprocesador
    watchdog = ap_status

    host = os.getenv('HOST', '0.0.0.0')
    port = int(os.getenv('PORT', '5002'))
    hostname = socket.gethostname()

    return jsonify({
        'success': True,
        'services': {
            # Compat con consumidores legacy del frontend
            'database': _status_label(db_ok),
            'ollama': _status_label(ollama_ok),
            'storage': _status_label(storage_ok),
            'pwa': _status_label(pwa_ok),
        },
        'detailed_services': {
            'database': {'ok': db_ok, 'path': str(DB_PATH), 'error': db_error},
            'ollama': {'ok': ollama_ok, 'base_url': ollama_url, 'error': ollama_error},
            'storage': {'ok': storage_ok, 'paths': storage_paths, 'error': storage_error},
            'pwa': {'ok': pwa_ok, 'required_assets': required_assets, 'error': pwa_error},
            'watchdog': {
                'ok': bool(watchdog.get('running')),
                'running': bool(watchdog.get('running')),
                'queued_files': int(watchdog.get('queued_files', 0)),
                'processed_today': int(watchdog.get('processed_today', 0)),
            }
        },
        'runtime': {
            'host': host,
            'port': port,
            'hostname': hostname,
            'python': f"{os.sys.version_info.major}.{os.sys.version_info.minor}.{os.sys.version_info.micro}",
            'flask_env': os.getenv('FLASK_ENV', 'development'),
        },
        'uptime': 'N/A',
        'last_deploy': datetime.now().strftime('%d/%m/%Y %H:%M'),
        'timestamp': datetime.now().isoformat(),
    }), 200

# ==================== LOGIN ENDPOINT ====================
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.json.get('email')
        password = request.json.get('password')
        
        if email == 'admin@lexdocs.com' and password == 'admin123':
            access_token = create_access_token(
                identity=email,
                additional_claims={'rol': 'ADMIN'}
            )
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
    print(f"🚀 LexDocsPro LITE v2.3.1 SIDEBAR CLASSIC iniciando en puerto 5002...")
    # Usamos threaded=True para manejar múltiples peticiones si es necesario
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", os.getenv("FLASK_PORT", "5002")))
    debug = os.getenv("DEBUG", "0").lower() in ("1", "true", "yes")
    app.run(host=host, port=port, debug=debug)
