#!/bin/bash

# ============================================================================
# LEXDOCSPRO LITE v2.0 - SCRIPT INSTALACIÓN COMPLETA
# Script que instala y configura TODO de cero
# ============================================================================

set -e

echo "════════════════════════════════════════════════════════════════"
echo "🚀 LEXDOCSPRO LITE v2.0 - INSTALACIÓN COMPLETA"
echo "════════════════════════════════════════════════════════════════"

# Variables
PROJECT_DIR="$HOME/Desktop/PROYECTOS/LexDocsPro-LITE"
BACKUP_DIR="$PROJECT_DIR/_backups_$(date +%s)"
VENV_DIR="$PROJECT_DIR/venv"
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')

echo "📁 Directorio proyecto: $PROJECT_DIR"
echo "🐍 Python: $PYTHON_VERSION"
echo ""

# ============================================================================
# PASO 1: BACKUP DE ARCHIVOS EXISTENTES
# ============================================================================
echo "📦 PASO 1: Haciendo backup de archivos existentes..."

if [ -d "$PROJECT_DIR" ]; then
    mkdir -p "$BACKUP_DIR"
    
    for file in run.py app.js document_generator.py; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            cp "$PROJECT_DIR/$file" "$BACKUP_DIR/$file.backup_$(date +%s)" 2>/dev/null || true
            echo "  ✅ Backup: $file"
        fi
    done
    
    for file in services/*.py; do
        if [ -f "$PROJECT_DIR/$file" ]; then
            mkdir -p "$BACKUP_DIR/services"
            cp "$PROJECT_DIR/$file" "$BACKUP_DIR/$file.backup_$(date +%s)" 2>/dev/null || true
        fi
    done
fi

echo ""

# ============================================================================
# PASO 2: CREAR ESTRUCTURA DE CARPETAS
# ============================================================================
echo "📂 PASO 2: Creando estructura de carpetas..."

mkdir -p "$PROJECT_DIR"
mkdir -p "$PROJECT_DIR/services"
mkdir -p "$PROJECT_DIR/templates"
mkdir -p "$PROJECT_DIR/static/js"
mkdir -p "$PROJECT_DIR/static/css"
mkdir -p "$HOME/Documents/LexDocsPro/Documentos"
mkdir -p "$HOME/Desktop/EXPEDIENTES/_GENERADOS"

echo "  ✅ Carpetas creadas"
echo ""

# ============================================================================
# PASO 3: CREAR ENTORNO VIRTUAL Y INSTALAR DEPENDENCIAS
# ============================================================================
echo "🔧 PASO 3: Configurando entorno Python..."

if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
    echo "  ✅ Entorno virtual creado"
fi

source "$VENV_DIR/bin/activate"

pip install --upgrade pip setuptools wheel > /dev/null 2>&1

echo "  📦 Instalando dependencias..."
pip install flask==3.0.0 > /dev/null 2>&1
pip install flask-cors==4.0.0 > /dev/null 2>&1
pip install requests==2.31.0 > /dev/null 2>&1
pip install python-dotenv==1.0.0 > /dev/null 2>&1
pip install PyPDF2==3.0.1 > /dev/null 2>&1
pip install pytesseract==0.3.10 > /dev/null 2>&1
pip install Pillow==10.0.0 > /dev/null 2>&1
pip install pytz==2023.3 > /dev/null 2>&1
pip install pymupdf==1.23.8 > /dev/null 2>&1

echo "  ✅ Dependencias instaladas"
echo ""

# ============================================================================
# PASO 4: CREAR ARCHIVO .env
# ============================================================================
echo "⚙️  PASO 4: Creando archivo .env..."

cat > "$PROJECT_DIR/.env" << 'EOF'
# ============================================================================
# LEXDOCSPRO LITE v2.0 - CONFIGURACIÓN
# ============================================================================

# IA LOCAL (OLLAMA)
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=lexdocs-legal

# APIS CLOUD (OPCIONALES)
GROQ_API_KEY=
PERPLEXITY_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
ANTHROPIC_API_KEY=

# CONFIGURACIÓN
FLASK_ENV=development
DEBUG=True
PORT=5002
HOST=0.0.0.0
EOF

echo "  ✅ .env creado"
echo ""

# ============================================================================
# PASO 5: CREAR run.py
# ============================================================================
echo "🐍 PASO 5: Generando run.py..."

cat > "$PROJECT_DIR/run.py" << 'EOFPYTHON'
#!/usr/bin/env python3
"""
LexDocsPro LITE v2.0 - Backend Flask
Gestor de documentos legales con IA
"""

import tempfile
import os
import re
import shutil
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

from services.ocr_service import OCRService
from services.ai_service import AIService
from services.document_generator import DocumentGenerator
from services.lexnet_analyzer import LexNetAnalyzer

app = Flask(__name__)
CORS(app)

# CONFIGURACIÓN
DEFAULT_AI_PROVIDER = os.getenv('DEFAULT_AI_PROVIDER', 'ollama')
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'lexdocs-legal')
GROQ_API_KEY = os.getenv('GROQ_API_KEY')
PERPLEXITY_API_KEY = os.getenv('PERPLEXITY_API_KEY')
PERPLEXITY_MODEL = os.getenv('PERPLEXITY_MODEL', 'llama-3.1-sonar-large-128k-online')
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

BASE_DIR = os.path.expanduser("~/Desktop/EXPEDIENTES")
GENERATED_DOCS_DIR = os.path.join(BASE_DIR, "_GENERADOS")

ocr_service = OCRService()
ai_service = AIService()
doc_generator = DocumentGenerator(ai_service)
lexnet_analyzer = LexNetAnalyzer(ai_service)

os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)

print("=" * 60)
print("🚀 LexDocsPro LITE v2.0 - Sistema Legal Multi-IA")
print("=" * 60)
print(f"📁 Base: {BASE_DIR}")
print(f"📄 Generados: {GENERATED_DOCS_DIR}")
print("=" * 60)

# ============================================================================
# RUTAS
# ============================================================================

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files/list')
def list_files():
    try:
        path = request.args.get('path', '')
        full_path = os.path.join(BASE_DIR, path) if path else BASE_DIR
        
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
        
        folders = []
        files = []
        
        for item in os.listdir(full_path):
            if item.startswith('.'):
                continue
            
            item_path = os.path.join(full_path, item)
            rel_path = os.path.join(path, item) if path else item
            
            if os.path.isdir(item_path):
                folders.append({'name': item, 'path': rel_path})
            elif item.lower().endswith(('.pdf', '.jpg', '.jpeg', '.png', '.docx')):
                files.append({'name': item, 'path': rel_path})
        
        return jsonify({
            'success': True,
            'files': files,
            'folders': folders
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ai/providers')
def get_providers():
    try:
        providers = ai_service.get_available_providers()
        return jsonify({
            'success': True,
            'providers': providers
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        message = data.get('message', '')
        provider = data.get('provider', 'ollama')
        
        if not message:
            return jsonify({'success': False, 'error': 'Mensaje vacío'})
        
        response = ai_service.consultar(message, '', provider, 'standard')
        
        return jsonify({
            'success': True,
            'response': response
        })
    except Exception as e:
        print(f"Error en chat: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents/generate', methods=['POST'])
def generate_document():
    try:
        data = request.json
        doc_type = data.get('doc_type')
        form_data = data.get('data', {})
        provider = data.get('provider', 'ollama')
        
        if not doc_type:
            return jsonify({'success': False, 'error': 'Tipo de documento no especificado'})
        
        result = doc_generator.generate(doc_type, form_data, provider)
        
        if isinstance(result, dict):
            if not result.get('success', False):
                return jsonify({
                    'success': False,
                    'error': result.get('error', 'Error generando documento')
                })
            content = result.get('content', '')
            filename = result.get('filename', f'{doc_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
        else:
            content = result
            filename = f'{doc_type}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt'
        
        filepath = os.path.join(GENERATED_DOCS_DIR, filename)
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })
    except Exception as e:
        print(f"Error generando documento: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/lexnet/analyze', methods=['POST'])
def lexnet_analyze():
    try:
        provider = request.form.get('provider', 'ollama') if 'files' in request.files else request.json.get('provider', 'ollama')
        
        textos = {}
        
        if 'files' in request.files:
            files = request.files.getlist('files')
            
            for file in files:
                try:
                    temp_dir = tempfile.mkdtemp()
                    temp_path = os.path.join(temp_dir, file.filename)
                    file.save(temp_path)
                    
                    if file.filename.lower().endswith('.pdf'):
                        import fitz
                        doc = fitz.open(temp_path)
                        textos[file.filename] = ''.join([page.get_text() for page in doc])
                        doc.close()
                    else:
                        textos[file.filename] = ocr_service.extraer_texto(temp_path)
                    
                    os.remove(temp_path)
                    os.rmdir(temp_dir)
                except Exception as e:
                    print(f"Error procesando {file.filename}: {e}")
        else:
            data = request.json
            textos = data.get('textos', {})
        
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
        
        return jsonify({
            'success': True,
            'analysis': analisis,
            'filename': filename
        })
    except Exception as e:
        print(f"Error en LexNET: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/ocr/process', methods=['POST'])
def ocr_process():
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'success': False, 'error': 'Nombre de archivo no especificado'})
        
        full_path = os.path.join(BASE_DIR, filename)
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'error': 'Archivo no encontrado'})
        
        text = ocr_service.extraer_texto(full_path)
        
        return jsonify({
            'success': True,
            'text': text
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5002))
    host = os.getenv('HOST', '0.0.0.0')
    
    print(f"🌐 Servidor iniciando en http://{host}:{port}")
    print("📝 Presiona Ctrl+C para detener")
    
    app.run(debug=True, host=host, port=port)
EOFPYTHON

chmod +x "$PROJECT_DIR/run.py"
echo "  ✅ run.py generado"
echo ""

# ============================================================================
# PASO 6: CREAR SERVICIOS
# ============================================================================
echo "⚙️  PASO 6: Generando servicios..."

# ocr_service.py
cat > "$PROJECT_DIR/services/ocr_service.py" << 'EOFOCR'
import pytesseract
from PIL import Image
import fitz
import io

class OCRService:
    def extraer_texto(self, filepath):
        try:
            if filepath.lower().endswith('.pdf'):
                doc = fitz.open(filepath)
                text = ''.join([page.get_text() for page in doc])
                doc.close()
                return text
            elif filepath.lower().endswith(('.jpg', '.jpeg', '.png')):
                img = Image.open(filepath)
                return pytesseract.image_to_string(img, lang='spa')
            else:
                return ""
        except Exception as e:
            print(f"Error OCR: {e}")
            return ""
EOFOCR

# ai_service.py
cat > "$PROJECT_DIR/services/ai_service.py" << 'EOFAI'
import requests
import os

class AIService:
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'lexdocs-legal')
    
    def get_available_providers(self):
        providers = ['ollama']
        if os.getenv('GROQ_API_KEY'):
            providers.append('groq')
        if os.getenv('PERPLEXITY_API_KEY'):
            providers.append('perplexity')
        if os.getenv('OPENAI_API_KEY'):
            providers.append('openai')
        return providers
    
    def consultar(self, mensaje, contexto='', provider='ollama', modo='standard'):
        try:
            if provider == 'ollama':
                return self._consultar_ollama(mensaje, contexto)
            elif provider == 'groq':
                return self._consultar_groq(mensaje, contexto)
            elif provider == 'perplexity':
                return self._consultar_perplexity(mensaje, contexto)
            else:
                return self._consultar_ollama(mensaje, contexto)
        except Exception as e:
            return f"Error: {str(e)}"
    
    def _consultar_ollama(self, mensaje, contexto):
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.ollama_model,
                    'prompt': f"{contexto}\n\n{mensaje}",
                    'stream': False
                },
                timeout=60
            )
            return response.json().get('response', 'Sin respuesta')
        except Exception as e:
            return f"Ollama error: {str(e)}"
    
    def _consultar_groq(self, mensaje, contexto):
        try:
            api_key = os.getenv('GROQ_API_KEY')
            response = requests.post(
                'https://api.groq.com/openai/v1/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.3-70b-versatile',
                    'messages': [
                        {'role': 'system', 'content': contexto},
                        {'role': 'user', 'content': mensaje}
                    ]
                },
                timeout=30
            )
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Groq error: {str(e)}"
    
    def _consultar_perplexity(self, mensaje, contexto):
        try:
            api_key = os.getenv('PERPLEXITY_API_KEY')
            response = requests.post(
                'https://api.perplexity.ai/chat/completions',
                headers={
                    'Authorization': f'Bearer {api_key}',
                    'Content-Type': 'application/json'
                },
                json={
                    'model': 'llama-3.1-sonar-large-128k-online',
                    'messages': [
                        {'role': 'system', 'content': contexto},
                        {'role': 'user', 'content': mensaje}
                    ]
                },
                timeout=30
            )
            return response.json()['choices'][0]['message']['content']
        except Exception as e:
            return f"Perplexity error: {str(e)}"
    
    def generar_documento(self, prompt, provider='ollama'):
        try:
            response = self.consultar(prompt, '', provider, 'document')
            return {
                'success': True,
                'content': response
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
EOFAI

# document_generator.py
cat > "$PROJECT_DIR/services/document_generator.py" << 'EOFDOC'
import os
from datetime import datetime
from pathlib import Path

class DocumentGenerator:
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.output_dir = Path.home() / "Documents" / "LexDocsPro" / "Documentos"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def get_templates(self):
        return {
            'demanda_civil': {
                'name': '⚖️ Demanda Civil',
                'description': 'Demanda para procedimiento civil ordinario',
                'fields': [
                    {'name': 'juzgado', 'label': 'Juzgado', 'type': 'text'},
                    {'name': 'demandante', 'label': 'Demandante', 'type': 'text'},
                    {'name': 'demandado', 'label': 'Demandado', 'type': 'text'},
                    {'name': 'hechos', 'label': 'Hechos', 'type': 'textarea'},
                    {'name': 'petitorio', 'label': 'Petitorio', 'type': 'textarea'}
                ]
            },
            'contestacion_demanda': {
                'name': '🛡️ Contestación a la Demanda',
                'description': 'Respuesta formal a demanda civil',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'demandado', 'label': 'Demandado', 'type': 'text'},
                    {'name': 'hechos_propios', 'label': 'Hechos propios', 'type': 'textarea'},
                    {'name': 'excepciones', 'label': 'Excepciones', 'type': 'textarea'}
                ]
            },
            'recurso_apelacion': {
                'name': '🔄 Recurso de Apelación',
                'description': 'Recurso contra sentencia',
                'fields': [
                    {'name': 'sentencia', 'label': 'Sentencia', 'type': 'text'},
                    {'name': 'recurrente', 'label': 'Recurrente', 'type': 'text'},
                    {'name': 'fundamentos', 'label': 'Fundamentos', 'type': 'textarea'}
                ]
            },
            'recurso_reposicion': {
                'name': '🔁 Recurso de Reposición',
                'description': 'Recurso contra autos',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'resolucion', 'label': 'Resolución', 'type': 'text'},
                    {'name': 'motivos', 'label': 'Motivos', 'type': 'textarea'}
                ]
            },
            'escrito_alegaciones': {
                'name': '📝 Escrito de Alegaciones',
                'description': 'Alegaciones en procedimiento',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'Parte', 'type': 'text'},
                    {'name': 'alegaciones', 'label': 'Alegaciones', 'type': 'textarea'}
                ]
            },
            'desistimiento': {
                'name': '🚫 Desistimiento',
                'description': 'Escrito de desistimiento',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'Parte', 'type': 'text'},
                    {'name': 'motivo', 'label': 'Motivo', 'type': 'textarea'}
                ]
            },
            'personacion': {
                'name': '👤 Personación',
                'description': 'Primera comparecencia',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'Parte', 'type': 'text'},
                    {'name': 'procurador', 'label': 'Procurador', 'type': 'text'}
                ]
            },
            'poder_procesal': {
                'name': '📜 Poder para Pleitos',
                'description': 'Poder procesal',
                'fields': [
                    {'name': 'poderdante', 'label': 'Poderdante', 'type': 'text'},
                    {'name': 'apoderado', 'label': 'Apoderado', 'type': 'text'},
                    {'name': 'ambito', 'label': 'Ámbito', 'type': 'text'}
                ]
            },
            'escrito_prueba': {
                'name': '🔬 Proposición de Prueba',
                'description': 'Medios de prueba',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'hechos', 'label': 'Hechos', 'type': 'textarea'},
                    {'name': 'pruebas', 'label': 'Pruebas', 'type': 'textarea'}
                ]
            },
            'burofax': {
                'name': '📮 Burofax',
                'description': 'Comunicación fehaciente',
                'fields': [
                    {'name': 'remitente', 'label': 'Remitente', 'type': 'text'},
                    {'name': 'destinatario', 'label': 'Destinatario', 'type': 'text'},
                    {'name': 'contenido', 'label': 'Contenido', 'type': 'textarea'}
                ]
            },
            'querella': {
                'name': '⚔️ Querella Criminal',
                'description': 'Acción penal',
                'fields': [
                    {'name': 'querellante', 'label': 'Querellante', 'type': 'text'},
                    {'name': 'querellado', 'label': 'Querellado', 'type': 'text'},
                    {'name': 'hechos', 'label': 'Hechos', 'type': 'textarea'},
                    {'name': 'delito', 'label': 'Delito', 'type': 'text'}
                ]
            }
        }
    
    def generate(self, doc_type, data, provider='ollama'):
        try:
            templates = self.get_templates()
            
            if doc_type not in templates:
                return {
                    'success': False,
                    'error': f'Tipo no válido: {doc_type}'
                }
            
            template = templates[doc_type]
            fields_text = '\n'.join([f"{k.upper()}: {v}" for k, v in data.items()])
            
            prompt = f"Genera un documento legal tipo {template['name']} con:\n\n{fields_text}\n\nUsa lenguaje jurídico profesional."
            
            response = self.ai_service.generar_documento(prompt, provider)
            
            if response.get('success'):
                content = response.get('content', '')
                filename = f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
                
                return {
                    'success': True,
                    'content': content,
                    'filename': filename
                }
            else:
                return response
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
EOFDOC

# lexnet_analyzer.py
cat > "$PROJECT_DIR/services/lexnet_analyzer.py" << 'EOFLEXNET'
class LexNetAnalyzer:
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
    def analizar_notificacion(self, textos, provider='ollama'):
        try:
            textos_str = '\n\n'.join([f"--- {k} ---\n{v[:1000]}" for k, v in textos.items()])
            
            prompt = f"""Analiza estos documentos judiciales españoles.

DOCUMENTOS:
{textos_str}

Extrae:
1. Cliente (demandante, demandado, etc.)
2. Tipo de documento
3. Fecha
4. Número de procedimiento
5. Plazos importantes
6. Acciones recomendadas

Responde en formato estructurado."""
            
            response = self.ai_service.consultar(prompt, '', provider, 'analysis')
            return response
        except Exception as e:
            return f"Error analizando: {str(e)}"
EOFLEXNET

touch "$PROJECT_DIR/services/__init__.py"

echo "  ✅ Servicios generados"
echo ""

# ============================================================================
# PASO 7: CREAR HTML Y JS
# ============================================================================
echo "🎨 PASO 7: Generando frontend..."

# index.html
cat > "$PROJECT_DIR/templates/index.html" << 'EOFHTML'
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexDocsPro LITE v2.0</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f5f5f5;
            color: #333;
        }
        header {
            background: #008B8B;
            color: white;
            padding: 20px;
            text-align: center;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
            border-bottom: 2px solid #ddd;
        }
        .tab-btn {
            padding: 12px 20px;
            background: none;
            border: none;
            cursor: pointer;
            border-bottom: 3px solid transparent;
            font-size: 16px;
            transition: all 0.3s;
        }
        .tab-btn:hover { border-color: #008B8B; }
        .tab-btn.active {
            border-color: #008B8B;
            color: #008B8B;
            font-weight: bold;
        }
        .tab-content {
            display: none;
            background: white;
            border-radius: 8px;
            padding: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }
        .tab-content.active { display: block; }
        
        .message {
            padding: 12px;
            margin: 10px 0;
            border-radius: 6px;
        }
        .message-user {
            background: #e3f2fd;
            text-align: right;
        }
        .message-ai {
            background: #f5f5f5;
            border-left: 3px solid #008B8B;
        }
        .message-system {
            background: #fff3cd;
            font-size: 12px;
        }
        
        textarea, input {
            width: 100%;
            padding: 10px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-family: inherit;
        }
        button {
            background: #008B8B;
            color: white;
            border: none;
            padding: 12px 20px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.2s;
        }
        button:hover { background: #006B6B; }
        button:disabled { opacity: 0.5; cursor: not-allowed; }
        
        .doc-btn {
            display: inline-block;
            padding: 15px;
            margin: 5px;
            background: #f0f0f0;
            border: 2px solid transparent;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.2s;
            text-align: center;
            min-width: 100px;
        }
        .doc-btn:hover { background: #e0e0e0; border-color: #008B8B; }
        .doc-btn.selected {
            background: #008B8B;
            color: white;
            border-color: #006B6B;
        }
        
        .form-group {
            margin: 15px 0;
        }
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 5px;
        }
        
        .file-list {
            list-style: none;
            max-height: 200px;
            overflow-y: auto;
        }
        .file-list li {
            padding: 8px;
            background: #f9f9f9;
            border-left: 3px solid #008B8B;
            margin: 5px 0;
        }
        
        #dropZone {
            border: 2px dashed #008B8B;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            background: #f9f9f9;
            cursor: pointer;
            transition: all 0.2s;
        }
        #dropZone:hover { background: #e3f2fd; }
        
        #chatOutput, #docOutput, #analysisOutput {
            border: 1px solid #ddd;
            border-radius: 4px;
            padding: 15px;
            max-height: 400px;
            overflow-y: auto;
            background: #fafafa;
            margin: 15px 0;
        }
        
        .status-bar {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 4px;
            font-size: 14px;
            opacity: 0.7;
            transition: opacity 0.3s;
        }
    </style>
</head>
<body>
    <header>
        <h1>⚖️ LexDocsPro LITE v2.0</h1>
        <p>Gestor de Documentos Legales con IA</p>
    </header>
    
    <div class="container">
        <!-- TABS -->
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('consulta')">💬 Consultas IA</button>
            <button class="tab-btn" onclick="switchTab('documentos')">📄 Generador Documentos</button>
            <button class="tab-btn" onclick="switchTab('lexnet')">📋 LexNET Analyzer</button>
        </div>
        
        <!-- TAB 1: CONSULTAS IA -->
        <div id="tab-consulta" class="tab-content active">
            <h2>💬 Consultas con IA</h2>
            
            <div class="form-group">
                <label>Proveedor IA:</label>
                <select id="chatProvider">
                    <option value="ollama">🏠 Ollama (Local)</option>
                </select>
            </div>
            
            <div id="chatOutput"></div>
            
            <div class="form-group">
                <textarea id="chatPrompt" placeholder="Escribe tu consulta..." rows="4"></textarea>
            </div>
            <button onclick="sendMessage()">Enviar</button>
        </div>
        
        <!-- TAB 2: GENERADOR DOCUMENTOS -->
        <div id="tab-documentos" class="tab-content">
            <h2>📄 Generador de Documentos</h2>
            
            <div class="form-group">
                <label>Tipo de Documento:</label>
                <div id="docTypes"></div>
            </div>
            
            <div class="form-group">
                <label>Proveedor IA:</label>
                <select id="docProvider">
                    <option value="ollama">🏠 Ollama (Local)</option>
                </select>
            </div>
            
            <div id="docForm"></div>
            <div id="docOutput"></div>
        </div>
        
        <!-- TAB 3: LEXNET -->
        <div id="tab-lexnet" class="tab-content">
            <h2>📋 LexNET Analyzer</h2>
            
            <div class="form-group">
                <label>Proveedor IA:</label>
                <select id="lexnetProvider">
                    <option value="ollama">🏠 Ollama (Local)</option>
                </select>
            </div>
            
            <div id="dropZone">
                <p>📁 Arrastra archivos aquí o haz clic para seleccionar</p>
                <input type="file" id="fileInput" multiple accept=".pdf,.jpg,.jpeg,.png" style="display:none;">
            </div>
            
            <ul id="lexnetFileList" class="file-list"></ul>
            
            <button onclick="analyzeLexnet()" style="width: 100%; margin-top: 15px;">Analizar</button>
            
            <div id="analysisOutput"></div>
        </div>
    </div>
    
    <div id="statusBar" class="status-bar">✅ Sistema listo</div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>
EOFHTML

# app.js
cat > "$PROJECT_DIR/static/js/app.js" << 'EOFJS'
const DOCUMENT_TYPES = {
    demanda_civil: { name: '⚖️ Demanda Civil', icon: '⚖️' },
    contestacion_demanda: { name: '🛡️ Contestación', icon: '🛡️' },
    recurso_apelacion: { name: '🔄 Apelación', icon: '🔄' },
    recurso_reposicion: { name: '🔁 Reposición', icon: '🔁' },
    escrito_alegaciones: { name: '📝 Alegaciones', icon: '📝' },
    desistimiento: { name: '🚫 Desistimiento', icon: '🚫' },
    personacion: { name: '👤 Personación', icon: '👤' },
    poder_procesal: { name: '📜 Poder', icon: '📜' },
    escrito_prueba: { name: '🔬 Prueba', icon: '🔬' },
    burofax: { name: '📮 Burofax', icon: '📮' },
    querella: { name: '⚔️ Querella', icon: '⚔️' }
};

let currentDocType = null;
let lexnetFiles = [];
let generatedDocContent = '';
let currentAnalysis = '';

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 LexDocsPro LITE iniciando...');
    loadAIProviders();
    initDocumentGenerator();
    initLexNetUploader();
    addMessage('system', '✅ Sistema listo. Puedes empezar a usar todas las funcionalidades.');
});

function switchTab(tab) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    
    document.getElementById(`tab-${tab}`).classList.add('active');
    event.target.classList.add('active');
    
    updateStatus(`📑 ${tab === 'consulta' ? 'Consultas' : tab === 'documentos' ? 'Generador' : 'LexNET'}`);
}

async function loadAIProviders() {
    try {
        const response = await fetch('/api/ai/providers');
        const data = await response.json();
        
        if (data.success && data.providers) {
            ['chatProvider', 'docProvider', 'lexnetProvider'].forEach(id => {
                const select = document.getElementById(id);
                select.innerHTML = '';
                data.providers.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p;
                    opt.textContent = p === 'ollama' ? '🏠 Ollama (Local)' : p;
                    select.appendChild(opt);
                });
            });
        }
    } catch (e) {
        console.error('Error cargando proveedores:', e);
    }
}

function initDocumentGenerator() {
    const container = document.getElementById('docTypes');
    container.innerHTML = '';
    
    for (const [key, doc] of Object.entries(DOCUMENT_TYPES)) {
        const btn = document.createElement('button');
        btn.className = 'doc-btn';
        btn.innerHTML = `${doc.icon}<br>${doc.name}`;
        btn.onclick = () => selectDocumentType(key, doc);
        container.appendChild(btn);
    }
}

function selectDocumentType(typeId, docType) {
    currentDocType = typeId;
    
    document.querySelectorAll('.doc-btn').forEach(b => b.classList.remove('selected'));
    event.target.classList.add('selected');
    
    const formContainer = document.getElementById('docForm');
    formContainer.innerHTML = `
        <div style="background: #f9f9f9; padding: 15px; border-radius: 6px; margin-bottom: 15px;">
            <h3>${docType.name}</h3>
        </div>
        <form onsubmit="generateDocument(event)">
            <div class="form-group">
                <label>Información del documento (puedes escribir libremente):</label>
                <textarea name="content" placeholder="Describe el contenido del documento..." rows="6" required></textarea>
            </div>
            <button type="submit">✏️ Generar Documento</button>
        </form>
    `;
    
    updateStatus(`📝 ${docType.name}`);
}

async function generateDocument(event) {
    event.preventDefault();
    
    const form = event.target;
    const content = form.content.value;
    const provider = document.getElementById('docProvider').value;
    
    updateStatus('⏳ Generando...');
    form.querySelector('button').disabled = true;
    
    try {
        const response = await fetch('/api/documents/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                doc_type: currentDocType,
                data: { content: content },
                provider: provider
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            generatedDocContent = result.content;
            document.getElementById('docOutput').innerHTML = `
                <div style="background: #d4edda; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
                    ✅ Documento generado
                </div>
                <pre style="background: white; padding: 15px; border-radius: 4px; overflow-y: auto; max-height: 300px; border: 1px solid #ddd;">${result.content}</pre>
                <div style="display: flex; gap: 10px; margin-top: 10px;">
                    <button onclick="copyDoc()" style="flex: 1;">📋 Copiar</button>
                    <button onclick="downloadDoc('${result.filename}')" style="flex: 1;">💾 Descargar</button>
                </div>
            `;
            updateStatus('✅ Documento listo');
        } else {
            alert('Error: ' + result.error);
        }
    } catch (e) {
        alert('Error: ' + e.message);
    } finally {
        form.querySelector('button').disabled = false;
    }
}

function copyDoc() {
    navigator.clipboard.writeText(generatedDocContent);
    alert('✅ Copiado al portapapeles');
}

function downloadDoc(filename) {
    const blob = new Blob([generatedDocContent], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = filename;
    a.click();
}

async function sendMessage() {
    const input = document.getElementById('chatPrompt');
    const provider = document.getElementById('chatProvider').value;
    
    if (!input.value.trim()) return;
    
    addMessage('user', input.value);
    updateStatus('⏳ IA respondiendo...');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                message: input.value,
                provider: provider
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            addMessage('ai', result.response);
            updateStatus('✅ Respuesta recibida');
        } else {
            addMessage('system', '❌ ' + result.error);
        }
    } catch (e) {
        addMessage('system', '❌ Error: ' + e.message);
    }
    
    input.value = '';
}

function addMessage(role, content) {
    const output = document.getElementById('chatOutput');
    const msg = document.createElement('div');
    msg.className = `message message-${role}`;
    msg.innerHTML = `<strong>${role === 'user' ? '👤 Tú' : role === 'ai' ? '🤖 IA' : '⚙️ Sistema'}:</strong> ${content.replace(/\n/g, '<br>')}`;
    output.appendChild(msg);
    output.scrollTop = output.scrollHeight;
}

function initLexNetUploader() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    
    dropZone.onclick = () => fileInput.click();
    
    dropZone.ondragover = (e) => {
        e.preventDefault();
        dropZone.style.background = '#e3f2fd';
    };
    
    dropZone.ondragleave = () => {
        dropZone.style.background = '#f9f9f9';
    };
    
    dropZone.ondrop = (e) => {
        e.preventDefault();
        handleLexnetFiles(e.dataTransfer.files);
    };
    
    fileInput.onchange = (e) => handleLexnetFiles(e.target.files);
}

function handleLexnetFiles(files) {
    lexnetFiles = Array.from(files);
    
    const list = document.getElementById('lexnetFileList');
    list.innerHTML = '';
    
    lexnetFiles.forEach((file, i) => {
        const li = document.createElement('li');
        li.textContent = `${i+1}. ${file.name} (${(file.size/1024).toFixed(1)} KB)`;
        list.appendChild(li);
    });
    
    updateStatus(`✅ ${lexnetFiles.length} archivo(s) seleccionado(s)`);
}

async function analyzeLexnet() {
    if (lexnetFiles.length === 0) {
        alert('Selecciona al menos 1 archivo');
        return;
    }
    
    updateStatus('⏳ Analizando...');
    
    const formData = new FormData();
    lexnetFiles.forEach(file => formData.append('files', file));
    formData.append('provider', document.getElementById('lexnetProvider').value);
    
    try {
        const response = await fetch('/api/lexnet/analyze', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            currentAnalysis = result.analysis;
            document.getElementById('analysisOutput').innerHTML = `
                <div style="background: #d4edda; padding: 10px; border-radius: 4px; margin-bottom: 10px;">
                    ✅ Análisis completado
                </div>
                <pre style="background: white; padding: 15px; border-radius: 4px; overflow-y: auto; max-height: 300px; border: 1px solid #ddd;">${result.analysis}</pre>
                <button onclick="exportAnalysis()" style="width: 100%; margin-top: 10px;">💾 Exportar Análisis</button>
            `;
            updateStatus('✅ Análisis listo');
        } else {
            alert('Error: ' + result.error);
        }
    } catch (e) {
        alert('Error: ' + e.message);
    }
}

function exportAnalysis() {
    const blob = new Blob([currentAnalysis], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analisis_${new Date().toISOString().split('T')[0]}.txt`;
    a.click();
}

function updateStatus(message) {
    const bar = document.getElementById('statusBar');
    bar.textContent = message;
    bar.style.opacity = '1';
    setTimeout(() => { bar.style.opacity = '0.7'; }, 5002);
}
EOFJS

echo "  ✅ Frontend generado"
echo ""

# ============================================================================
# PASO 8: RESUMEN Y FINALIZACIÓN
# ============================================================================
echo "🎉 INSTALACIÓN COMPLETADA"
echo "════════════════════════════════════════════════════════════════"
echo ""
echo "✅ Sistema instalado en: $PROJECT_DIR"
echo "✅ Entorno virtual: $VENV_DIR"
echo "✅ Documentos generados: $HOME/Documents/LexDocsPro/Documentos"
echo ""
echo "🚀 PARA INICIAR:"
echo ""
echo "  cd $PROJECT_DIR"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "🌐 Luego abre: http://localhost:5002"
echo ""
echo "════════════════════════════════════════════════════════════════"
echo ""
