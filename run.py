import tempfile
from flask import Flask, render_template, jsonify, request, send_file
import os
from datetime import datetime
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.document_generator import DocumentGenerator
from services.lexnet_analyzer import LexNetAnalyzer

app = Flask(__name__)

# Configuración
BASE_DIR = os.path.expanduser("~/Desktop/EXPEDIENTES")
GENERATED_DOCS_DIR = os.path.join(BASE_DIR, "_GENERADOS")

# Servicios
ocr_service = OCRService()
ai_service = AIService()
doc_generator = DocumentGenerator(ai_service)
lexnet_analyzer = LexNetAnalyzer(ai_service)  # ← AQUÍ estaba el error

# Asegurar que existe el directorio de generados
os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)

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
    data = request.json
    doc_type = data.get('type')
    form_data = data.get('data')
    provider = data.get('provider', 'ollama')
    
    try:
        content = doc_generator.generate(doc_type, form_data, provider)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{doc_type}_{timestamp}.txt"
        filepath = os.path.join(GENERATED_DOCS_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return jsonify({
            'success': True,
            'content': content,
            'filename': filename
        })
    except Exception as e:
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

if __name__ == '__main__':
    print("🚀 Iniciando LexDocsPro LITE v2.0...")
    print(f"📁 Directorio: {BASE_DIR}")
    print(f"📄 Documentos generados: {GENERATED_DOCS_DIR}")
    print("🌐 Abriendo navegador en http://localhost:5001")
    
    import webbrowser
    webbrowser.open('http://localhost:5001')
    
    app.run(debug=True, host='0.0.0.0', port=5001)
