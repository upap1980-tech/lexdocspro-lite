import tempfile
import os
import re
import shutil
from datetime import datetime
from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Servicios existentes
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.document_generator import DocumentGenerator
from services.lexnet_analyzer import LexNetAnalyzer

app = Flask(__name__)
CORS(app)

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
doc_generator = DocumentGenerator(ai_service)
lexnet_analyzer = LexNetAnalyzer(ai_service)

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
                print(f"⚠️  Ollama no disponible (código {response.status_code})")
                
        except requests.exceptions.ConnectionError:
            print("⚠️  Ollama no está corriendo → Intentando con APIs cloud...")
        except Exception as e:
            print(f"⚠️  Ollama error: {e}")

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
                print(f"⚠️  Groq error {response.status_code}")
                
        except Exception as e:
            print(f"⚠️  Groq falló: {e}")

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
            print(f"⚠️  Perplexity falló: {e}")

    print("❌ Todas las IAs fallaron → Usando fallback REGEX")
    return None, None


# ============================================
# RUTAS EXISTENTES (SIN CAMBIOS)
# ============================================

@app.route('/')
def index():
    return render_template('index.html')

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
            print(f"❌ ERRO: result no es dict, es {type(result)}")
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
    """Extraer texto de archivo subido"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió archivo'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'})
        
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        try:
            text = ocr_service.extraer_texto(temp_path)
            
            return jsonify({
                'success': True,
                'text': text,
                'filename': file.filename
            })
            
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)
            if os.path.exists(temp_dir):
                os.rmdir(temp_dir)
    
    except Exception as e:
        print(f"Error en OCR upload: {str(e)}")
        return jsonify({'success': False, 'error': str(e)})

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
# ENDPOINTS iCLOUD (SIN CAMBIOS)
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
                    print(f"⚠️  Error parseando JSON: {e}")
        
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


if __name__ == '__main__':
    print("🚀 Iniciando LexDocsPro LITE v2.0...")
    print(f"📁 Directorio: {BASE_DIR}")
    print(f"📄 Documentos generados: {GENERATED_DOCS_DIR}")
    print("🌐 Abriendo navegador en http://localhost:5011")
    
    import webbrowser
    webbrowser.open('http://localhost:5011')
    
    app.run(debug=True, host='0.0.0.0', port=5001)

