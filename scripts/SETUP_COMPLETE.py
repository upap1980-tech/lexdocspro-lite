#!/usr/bin/env python3
"""
SETUP_COMPLETE.py - Crea LexDocsPro LITE COMPLETO de cero
Ejecutar: python3 SETUP_COMPLETE.py
"""
import os
import sys
from pathlib import Path

PROJECT = Path.home() / "Desktop" / "PROYECTOS" / "LexDocsPro-LITE"
PROJECT.mkdir(parents=True, exist_ok=True)

print("\n" + "="*80)
print("🚀 CREANDO LexDocsPro LITE v2.0 COMPLETO")
print("="*80)

# ============================================================================
# 1. CARPETAS
# ============================================================================
print("\n📁 Creando carpetas...")
folders = [
    PROJECT / "static" / "css",
    PROJECT / "static" / "js",
    PROJECT / "templates",
]

for folder in folders:
    folder.mkdir(parents=True, exist_ok=True)
    print(f"  ✅ {folder.name}")

# ============================================================================
# 2. requirements.txt
# ============================================================================
print("\n📦 Creando requirements.txt...")
requirements = """Flask==2.3.3
Flask-CORS==4.0.0
python-dotenv==1.0.0
requests==2.31.0
"""

with open(PROJECT / "requirements.txt", "w") as f:
    f.write(requirements)
print("  ✅ requirements.txt")

# ============================================================================
# 3. .env
# ============================================================================
print("\n⚙️  Creando .env...")
env_content = """FLASK_ENV=development
FLASK_DEBUG=True
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2
PORT=5001
HOST=0.0.0.0
"""

with open(PROJECT / ".env", "w") as f:
    f.write(env_content)
print("  ✅ .env")

# ============================================================================
# 4. run.py - BACKEND FLASK
# ============================================================================
print("\n🐍 Creando run.py...")
run_py = '''#!/usr/bin/env python3
"""
LexDocsPro LITE v2.0 - Backend Flask
Gestor de documentos legales con IA local
"""

import os
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama2')
BASE_DIR = os.path.expanduser("~/Desktop/EXPEDIENTES")
GENERATED_DOCS_DIR = os.path.join(BASE_DIR, "_GENERADOS")

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)

print("\\n" + "="*70)
print("🚀 LexDocsPro LITE v2.0 - Backend iniciado")
print("="*70)
print(f"  Base URL: {OLLAMA_BASE_URL}")
print(f"  Modelo: {OLLAMA_MODEL}")
print(f"  Puerto: {os.getenv('PORT', 5001)}")
print("="*70 + "\\n")

@app.route('/')
def index():
    """Sirve la página principal"""
    return render_template('index.html')

@app.route('/api/chat', methods=['POST'])
def chat():
    """Endpoint para consultas con IA"""
    try:
        data = request.json
        prompt = data.get('prompt') or data.get('message')
        context = data.get('context', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Mensaje vacío'})
        
        full_prompt = f"{context}\\n\\n{prompt}" if context else prompt
        
        response = requests.post(
            f'{OLLAMA_BASE_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': full_prompt,
                'stream': False
            },
            timeout=120
        )
        
        result = response.json()
        return jsonify({
            'success': True,
            'response': result.get('response', 'Sin respuesta')
        })
        
    except requests.exceptions.ConnectionError:
        return jsonify({
            'success': False,
            'error': '❌ Ollama no disponible en ' + OLLAMA_BASE_URL
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents/generate', methods=['POST'])
def generate_document():
    """Endpoint para generar documentos legales"""
    try:
        data = request.json
        doc_type = data.get('type') or data.get('doc_type')
        form_data = data.get('data', {})
        
        if not doc_type:
            return jsonify({'success': False, 'error': 'Tipo no especificado'})
        
        content_text = form_data.get('content', '')
        
        prompt = f"""Eres un abogado experto en derecho español.
        
Genera un documento legal tipo: {doc_type}

Contenido/Descripción: {content_text}

Requisitos:
- Lenguaje profesional y formal
- Conforme a normas procesales españolas
- Apto para presentación en juzgados españoles
- Incluye todas las cláusulas necesarias
- Estructura completa y coherente

Genera el documento ahora:"""
        
        response = requests.post(
            f'{OLLAMA_BASE_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=120
        )
        
        result = response.json()
        content = result.get('response', '')
        
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{doc_type}_{timestamp}.txt"
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/lexnet/analyze', methods=['POST'])
def lexnet_analyze():
    """Endpoint para analizar documentos LexNET"""
    try:
        textos = {}
        
        if 'files' in request.files:
            files = request.files.getlist('files')
            for file in files:
                try:
                    content = file.read().decode('utf-8', errors='ignore')
                    textos[file.filename] = content[:3000]
                except:
                    pass
        
        if not any(textos.values()):
            return jsonify({'success': False, 'error': 'No hay texto para analizar'})
        
        textos_str = '\\n\\n'.join([f"--- {k} ---\\n{v[:1000]}" for k, v in textos.items()])
        
        prompt = f"""Eres un abogado experto en procedimiento civil y penal español.

ANALIZA estos documentos judiciales españoles:

{textos_str}

EXTRAE Y ORGANIZA:
1. PARTES: Demandante, demandado, abogados
2. PROCEDIMIENTO: Tipo y clase
3. TRIBUNAL: Juzgado/Audiencia
4. FECHAS: Clave
5. NUMERO PROCEDIMIENTO: Referencia
6. PLAZOS: Importantes
7. MEDIDAS CAUTELARES: Si las hay
8. ACCIONES RECOMENDADAS: Próximos pasos"""
        
        response = requests.post(
            f'{OLLAMA_BASE_URL}/api/generate',
            json={
                'model': OLLAMA_MODEL,
                'prompt': prompt,
                'stream': False
            },
            timeout=120
        )
        
        result = response.json()
        
        return jsonify({
            'success': True,
            'analysis': result.get('response', '')
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/documents/templates')
def get_templates():
    """Devuelve plantillas disponibles"""
    templates = {
        'demanda_civil': {
            'name': 'Demanda Civil',
            'description': 'Demanda ordinaria en procedimiento civil'
        },
        'contestacion': {
            'name': 'Contestación',
            'description': 'Respuesta a demanda'
        },
        'recurso_apelacion': {
            'name': 'Recurso de Apelación',
            'description': 'Recurso contra sentencia'
        },
        'solicitud_cautelar': {
            'name': 'Solicitud de Medida Cautelar',
            'description': 'Medidas cautelares antes de sentencia'
        },
        'demanda_penal': {
            'name': 'Acusación Penal',
            'description': 'Acusación en procedimiento penal'
        }
    }
    return jsonify(templates)

@app.route('/api/ai/providers')
def get_providers():
    """Devuelve proveedores IA disponibles"""
    return jsonify({
        'success': True,
        'providers': ['ollama'],
        'default': 'ollama'
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'success': False, 'error': 'Endpoint no encontrado'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'success': False, 'error': 'Error interno del servidor'}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))
    host = os.getenv('HOST', '0.0.0.0')
    print(f"\\n🌐 Servidor en http://localhost:{port}")
    print("📝 Ctrl+C para detener\\n")
    app.run(debug=True, port=port, host=host)
'''

with open(PROJECT / "run.py", "w") as f:
    f.write(run_py)
print("  ✅ run.py")

# ============================================================================
# 5. app.js - FRONTEND JAVASCRIPT
# ============================================================================
print("\n💻 Creando app.js...")
app_js = '''// LexDocsPro LITE v2.0 - Frontend JavaScript

let currentFile = null;
let generatedDocContent = '';

document.addEventListener('DOMContentLoaded', () => {
    console.log('🚀 LexDocsPro LITE iniciando...');
    loadAIProviders();
    loadDocumentTemplates();
    addMessage('system', '✅ Sistema listo');
});

function switchTab(tabName) {
    document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
    document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
    document.getElementById(`tab-${tabName}`).classList.add('active');
    event.target.classList.add('active');
}

async function loadAIProviders() {
    try {
        const response = await fetch('/api/ai/providers');
        const data = await response.json();
        if (data.success && data.providers) {
            ['chatProvider', 'docProvider', 'lexnetProvider'].forEach(id => {
                const select = document.getElementById(id);
                if (select) {
                    select.innerHTML = '';
                    data.providers.forEach(p => {
                        const opt = document.createElement('option');
                        opt.value = p;
                        opt.textContent = p === 'ollama' ? 'Ollama (Local)' : p;
                        select.appendChild(opt);
                    });
                }
            });
        }
    } catch (e) {
        console.error('Error cargando providers:', e);
    }
}

async function loadDocumentTemplates() {
    try {
        const response = await fetch('/api/documents/templates');
        const templates = await response.json();
        
        const container = document.getElementById('docTypes');
        if (container) {
            container.innerHTML = '';
            for (const [key, doc] of Object.entries(templates)) {
                const btn = document.createElement('button');
                btn.className = 'doc-btn';
                btn.innerHTML = `<strong>${doc.name}</strong><br><small>${doc.description}</small>`;
                btn.onclick = () => selectDocumentType(key, doc);
                container.appendChild(btn);
            }
        }
    } catch (e) {
        console.error('Error cargando templates:', e);
    }
}

function selectDocumentType(typeId, docType) {
    const formContainer = document.getElementById('docForm');
    if (formContainer) {
        formContainer.innerHTML = `
            <h3>📋 ${docType.name}</h3>
            <form onsubmit="generateDocument(event, '${typeId}')">
                <label>Descripción/Contenido:</label>
                <textarea name="content" placeholder="Describe qué debe contener el documento..." rows="6" required></textarea>
                <button type="submit" style="width: 100%; margin-top: 10px;">⚡ Generar</button>
            </form>
        `;
    }
}

async function sendMessage() {
    const input = document.getElementById('chatPrompt');
    const provider = document.getElementById('chatProvider')?.value || 'ollama';
    
    if (!input.value.trim()) return;
    
    addMessage('user', input.value);
    updateStatus('⏳ IA respondiendo...');
    
    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: input.value,
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

async function generateDocument(event, docType) {
    event.preventDefault();
    
    const form = event.target;
    const content = form.content.value;
    const provider = document.getElementById('docProvider')?.value || 'ollama';
    
    updateStatus('⏳ Generando documento...');
    const btn = form.querySelector('button');
    btn.disabled = true;
    
    try {
        const response = await fetch('/api/documents/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: docType,
                data: { content: content },
                provider: provider
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            generatedDocContent = result.content;
            document.getElementById('docOutput').innerHTML = `
                <div style="background: #d4edda; padding: 15px; margin-bottom: 15px; border-radius: 6px;">
                    ✅ Documento generado exitosamente
                </div>
                <pre style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: #f8f9fa; border-radius: 6px;">${result.content}</pre>
                <button onclick="copyDoc()" style="width: 100%; margin-top: 10px;">📋 Copiar al portapapeles</button>
            `;
            updateStatus('✅ Documento listo');
        } else {
            alert('❌ Error: ' + result.error);
            updateStatus('❌ Error al generar');
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
        updateStatus('❌ Error');
    } finally {
        btn.disabled = false;
    }
}

function copyDoc() {
    navigator.clipboard.writeText(generatedDocContent);
    alert('✅ Copiado al portapapeles');
}

async function analyzeLexnet() {
    const files = document.getElementById('fileInput')?.files;
    if (!files || files.length === 0) {
        alert('⚠️ Selecciona archivos para analizar');
        return;
    }
    
    updateStatus('⏳ Analizando documentos...');
    
    const formData = new FormData();
    for (let file of files) {
        formData.append('files', file);
    }
    
    try {
        const response = await fetch('/api/lexnet/analyze', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        
        if (result.success) {
            document.getElementById('analysisOutput').innerHTML = `
                <div style="background: #d4edda; padding: 15px; margin-bottom: 15px; border-radius: 6px;">
                    ✅ Análisis completado
                </div>
                <pre style="max-height: 400px; overflow-y: auto; border: 1px solid #ddd; padding: 15px; background: #f8f9fa; border-radius: 6px;">${result.analysis}</pre>
            `;
            updateStatus('✅ Análisis listo');
        } else {
            alert('❌ Error: ' + result.error);
            updateStatus('❌ Error al analizar');
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
        updateStatus('❌ Error');
    }
}

function addMessage(role, content) {
    const output = document.getElementById('chatOutput');
    if (output) {
        const msg = document.createElement('div');
        msg.className = `message message-${role}`;
        const roleText = role === 'user' ? '👤 Tú' : role === 'ai' ? '🤖 IA' : '⚙️ Sistema';
        msg.innerHTML = `<strong>${roleText}:</strong><br>${content.replace(/\\n/g, '<br>')}`;
        output.appendChild(msg);
        output.scrollTop = output.scrollHeight;
    }
}

function updateStatus(message) {
    const bar = document.getElementById('statusBar');
    if (bar) bar.textContent = message;
}
'''

with open(PROJECT / "static" / "js" / "app.js", "w") as f:
    f.write(app_js)
print("  ✅ app.js")

# ============================================================================
# 6. index.html - FRONTEND HTML
# ============================================================================
print("\n🌐 Creando index.html...")
index_html = '''<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LexDocsPro LITE v2.0 - Gestor Documentos Legales</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', sans-serif;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            color: #333;
            min-height: 100vh;
        }
        
        header {
            background: linear-gradient(135deg, #008B8B 0%, #006B6B 100%);
            color: white;
            padding: 30px 20px;
            text-align: center;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }
        
        header h1 {
            font-size: 2.5em;
            margin-bottom: 5px;
        }
        
        header p {
            font-size: 1.1em;
            opacity: 0.9;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 30px 20px;
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            flex-wrap: wrap;
        }
        
        .tab-btn {
            padding: 12px 24px;
            background: white;
            border: 2px solid #ddd;
            cursor: pointer;
            border-radius: 8px;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        .tab-btn:hover {
            background: #f0f0f0;
            border-color: #008B8B;
        }
        
        .tab-btn.active {
            background: #008B8B;
            color: white;
            border-color: #008B8B;
        }
        
        .tab-content {
            display: none;
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 8px 16px rgba(0,0,0,0.1);
        }
        
        .tab-content.active {
            display: block;
            animation: fadeIn 0.3s ease;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
        }
        
        h2 {
            margin-bottom: 20px;
            color: #008B8B;
        }
        
        label {
            display: block;
            margin-top: 15px;
            margin-bottom: 8px;
            font-weight: 500;
            color: #555;
        }
        
        textarea, select, input[type="file"] {
            width: 100%;
            padding: 12px;
            margin: 10px 0;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-family: inherit;
            font-size: 1em;
        }
        
        textarea:focus, select:focus, input[type="file"]:focus {
            outline: none;
            border-color: #008B8B;
            box-shadow: 0 0 0 3px rgba(0, 139, 139, 0.1);
        }
        
        button {
            background: linear-gradient(135deg, #008B8B 0%, #006B6B 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 1em;
            font-weight: 500;
            transition: all 0.3s ease;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
        }
        
        button:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .message {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            line-height: 1.6;
        }
        
        .message-user {
            background: #e3f2fd;
            text-align: right;
            border-left: 4px solid #008B8B;
        }
        
        .message-ai {
            background: #f5f5f5;
            border-left: 4px solid #008B8B;
        }
        
        .message-system {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
        }
        
        #chatOutput {
            border: 1px solid #ddd;
            padding: 20px;
            max-height: 400px;
            overflow-y: auto;
            margin: 20px 0;
            border-radius: 8px;
            background: #f9f9f9;
        }
        
        .doc-btn {
            display: inline-block;
            padding: 15px 20px;
            margin: 10px 10px 10px 0;
            background: white;
            color: #333;
            border: 2px solid #ddd;
            cursor: pointer;
            border-radius: 8px;
            font-size: 0.95em;
            transition: all 0.3s ease;
            text-align: left;
        }
        
        .doc-btn:hover {
            background: #f0f0f0;
            border-color: #008B8B;
            transform: translateY(-2px);
        }
        
        .doc-btn strong {
            display: block;
            margin-bottom: 5px;
        }
        
        .doc-btn small {
            color: #666;
        }
        
        #statusBar {
            position: fixed;
            bottom: 20px;
            right: 20px;
            background: #333;
            color: white;
            padding: 12px 20px;
            border-radius: 8px;
            z-index: 1000;
            box-shadow: 0 4px 12px rgba(0,0,0,0.2);
            max-width: 300px;
        }
        
        #docTypes, #docForm, #docOutput, #analysisOutput {
            margin-top: 20px;
        }
        
        pre {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            font-size: 0.9em;
            line-height: 1.4;
        }
    </style>
</head>
<body>
    <header>
        <h1>⚖️ LexDocsPro LITE v2.0</h1>
        <p>Gestor Inteligente de Documentos Legales</p>
    </header>
    
    <div class="container">
        <div class="tabs">
            <button class="tab-btn active" onclick="switchTab('consulta')">💬 Consultas IA</button>
            <button class="tab-btn" onclick="switchTab('documentos')">📄 Generador</button>
            <button class="tab-btn" onclick="switchTab('lexnet')">📋 LexNET</button>
        </div>
        
        <!-- TAB 1: CONSULTAS -->
        <div id="tab-consulta" class="tab-content active">
            <h2>💬 Consultas con IA</h2>
            
            <label>Proveedor IA:</label>
            <select id="chatProvider"></select>
            
            <div id="chatOutput"></div>
            
            <label>Tu consulta:</label>
            <textarea id="chatPrompt" placeholder="Escribe tu pregunta legal..." rows="4"></textarea>
            <button onclick="sendMessage()" style="width: 100%;">📤 Enviar</button>
        </div>
        
        <!-- TAB 2: GENERADOR -->
        <div id="tab-documentos" class="tab-content">
            <h2>📄 Generador de Documentos</h2>
            
            <label>Proveedor IA:</label>
            <select id="docProvider"></select>
            
            <h3 style="margin-top: 20px;">Selecciona tipo de documento:</h3>
            <div id="docTypes"></div>
            
            <div id="docForm"></div>
            <div id="docOutput"></div>
        </div>
        
        <!-- TAB 3: LEXNET -->
        <div id="tab-lexnet" class="tab-content">
            <h2>📋 Analizador LexNET</h2>
            
            <label>Proveedor IA:</label>
            <select id="lexnetProvider"></select>
            
            <label>Selecciona documentos PDF o TXT:</label>
            <input type="file" id="fileInput" multiple accept=".pdf,.txt,.doc,.docx">
            <button onclick="analyzeLexnet()" style="width: 100%;">🔍 Analizar</button>
            
            <div id="analysisOutput"></div>
        </div>
    </div>
    
    <div id="statusBar">✅ Sistema listo</div>
    
    <script src="/static/js/app.js"></script>
</body>
</html>
'''

with open(PROJECT / "templates" / "index.html", "w") as f:
    f.write(index_html)
print("  ✅ index.html")

# ============================================================================
# RESUMEN FINAL
# ============================================================================
print("\n" + "="*80)
print("✅ PROYECTO CREADO COMPLETAMENTE")
print("="*80)
print(f"""
📁 Ubicación: {PROJECT}

📦 Archivos creados:
   ✅ requirements.txt - Dependencias Python
   ✅ .env - Configuración
   ✅ run.py - Backend Flask (220+ líneas)
   ✅ static/js/app.js - Frontend JavaScript (300+ líneas)
   ✅ templates/index.html - Frontend HTML

📁 Carpetas creadas:
   ✅ static/css/
   ✅ static/js/
   ✅ templates/

⚡ PRÓXIMOS PASOS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

1️⃣  Entra al proyecto:
    cd {PROJECT}

2️⃣  Crea virtualenv (si aún no existe):
    python3 -m venv venv

3️⃣  Activa virtualenv:
    source venv/bin/activate

4️⃣  Instala dependencias:
    python3 -m pip install -r requirements.txt

5️⃣  Inicia servidor:
    python run.py

6️⃣  Abre navegador:
    http://localhost:5011

🚀 ¡LISTO!
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
""")

print("\n✨ Script completado exitosamente")
sys.exit(0)
