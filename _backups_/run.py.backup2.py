import tempfile
#!/usr/bin/env python3
"""
LexDocsPro LITE v2.0 - Gestor de Documentos Legales
Versión mejorada con multi-IA y generación de documentos
"""
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from pathlib import Path
import webbrowser
from threading import Timer

from services.file_service import FileService
from services.ocr_service import OCRService
from services.ai_service import AIService
from services.document_generator import DocumentGenerator

BASE_DIR = Path(__file__).parent
EXPEDIENTES_DIR = Path.home() / "Desktop" / "EXPEDIENTES"
EXPEDIENTES_DIR.mkdir(exist_ok=True)

GENERATED_DOCS_DIR = EXPEDIENTES_DIR / "_GENERADOS"
GENERATED_DOCS_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
CORS(app)

# Servicios
file_service = FileService(EXPEDIENTES_DIR)
ocr_service = OCRService()
ai_service = AIService()
doc_generator = DocumentGenerator(ai_service)

@app.route('/')
def index():
    """Página principal"""
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    """Listar archivos del directorio"""
    try:
        path = request.args.get('path', '')
        files = file_service.list_directory(path)
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/<path:filename>')
def serve_pdf(filename):
    """Servir archivo PDF"""
    try:
        file_path = EXPEDIENTES_DIR / filename
        if file_path.exists() and file_path.suffix.lower() == '.pdf':
            return send_file(file_path, mimetype='application/pdf')
        return jsonify({'error': 'Archivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr', methods=['POST'])
def extract_text():
    """Extraer texto con OCR"""
    try:
        data = request.json
        filename = data.get('filename')
        file_path = EXPEDIENTES_DIR / filename
        
        if not file_path.exists():
            return jsonify({'error': 'Archivo no encontrado'}), 404
        
        text = ocr_service.extract_text(file_path)
        return jsonify({'text': text})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """Chat con IA (multi-proveedor)"""
    try:
        data = request.json
        prompt = data.get('prompt')
        context = data.get('context', '')
        provider = data.get('provider', None)  # ollama, openai, perplexity, etc.
        mode = data.get('mode', 'standard')  # standard, deep, research
        
        result = ai_service.chat(prompt, context, provider, mode)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai/providers', methods=['GET'])
def get_providers():
    """Listar proveedores de IA disponibles"""
    try:
        providers = ai_service.get_available_providers()
        return jsonify({
            'providers': providers,
            'default': ai_service.default_provider
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/generate', methods=['POST'])
def generate_document():
    """Generar documento jurídico profesional"""
    try:
        data = request.json
        doc_type = data.get('type')  # demanda, recurso, contrato, escrito, burofax
        doc_data = data.get('data', {})
        provider = data.get('provider', 'ollama')
        
        # Validar tipo de documento
        valid_types = ['demanda', 'recurso', 'contrato', 'escrito', 'burofax']
        if doc_type not in valid_types:
            return jsonify({'error': f'Tipo no válido. Usa: {", ".join(valid_types)}'}), 400
        
        # Generar documento
        document_content = doc_generator.generate_document(doc_type, doc_data, provider)
        
        # Guardar documento
        filename = f"{doc_type}_{data.get('data', {}).get('nombre', 'sin_nombre')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = GENERATED_DOCS_DIR / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(document_content)
        
        return jsonify({
            'success': True,
            'content': document_content,
            'filename': filename,
            'path': str(file_path)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/documents/templates', methods=['GET'])
def get_document_templates():
    """Obtener plantillas de documentos disponibles"""
    templates = {
        'demanda': {
            'name': 'Demanda Judicial',
            'description': 'Demanda profesional para procedimientos civiles',
            'fields': [
                {'name': 'tipo_procedimiento', 'label': 'Tipo de Procedimiento', 'type': 'select', 'options': ['Ordinario', 'Verbal', 'Monitorio']},
                {'name': 'juzgado', 'label': 'Juzgado', 'type': 'text'},
                {'name': 'materia', 'label': 'Materia', 'type': 'text'},
                {'name': 'demandante', 'label': 'Datos del Demandante', 'type': 'textarea'},
                {'name': 'demandado', 'label': 'Datos del Demandado', 'type': 'textarea'},
                {'name': 'hechos', 'label': 'Hechos', 'type': 'textarea'},
                {'name': 'peticiones', 'label': 'Peticiones', 'type': 'textarea'},
                {'name': 'documentos', 'label': 'Documentos Adjuntos', 'type': 'textarea'}
            ]
        },
        'recurso': {
            'name': 'Recurso',
            'description': 'Recurso de apelación, casación o reposición',
            'fields': [
                {'name': 'tipo_recurso', 'label': 'Tipo de Recurso', 'type': 'select', 'options': ['Apelación', 'Casación', 'Reposición', 'Súplica']},
                {'name': 'resolucion', 'label': 'Resolución Recurrida', 'type': 'textarea'},
                {'name': 'tribunal', 'label': 'Tribunal', 'type': 'text'},
                {'name': 'recurrente', 'label': 'Datos del Recurrente', 'type': 'textarea'},
                {'name': 'recurrido', 'label': 'Parte Recurrida', 'type': 'textarea'},
                {'name': 'motivos', 'label': 'Motivos del Recurso', 'type': 'textarea'},
                {'name': 'pretension', 'label': 'Pretensión', 'type': 'textarea'}
            ]
        },
        'contrato': {
            'name': 'Contrato',
            'description': 'Contrato civil o mercantil',
            'fields': [
                {'name': 'tipo_contrato', 'label': 'Tipo de Contrato', 'type': 'select', 'options': ['Arrendamiento', 'Compraventa', 'Prestación de servicios', 'Sociedad', 'Obra']},
                {'name': 'parte1', 'label': 'Primera Parte', 'type': 'textarea'},
                {'name': 'parte2', 'label': 'Segunda Parte', 'type': 'textarea'},
                {'name': 'objeto', 'label': 'Objeto del Contrato', 'type': 'textarea'},
                {'name': 'condiciones', 'label': 'Condiciones Específicas', 'type': 'textarea'},
                {'name': 'plazo_precio', 'label': 'Plazo y Precio', 'type': 'textarea'}
            ]
        },
        'escrito': {
            'name': 'Escrito Procesal',
            'description': 'Escrito simple de trámite o alegaciones',
            'fields': [
                {'name': 'tipo_escrito', 'label': 'Tipo', 'type': 'select', 'options': ['Alegaciones', 'Solicitud', 'Personación', 'Subsanación']},
                {'name': 'destinatario', 'label': 'Destinatario', 'type': 'text'},
                {'name': 'procedimiento', 'label': 'Procedimiento', 'type': 'text'},
                {'name': 'solicitante', 'label': 'Solicitante', 'type': 'textarea'},
                {'name': 'solicitud', 'label': 'Solicitud', 'type': 'textarea'},
                {'name': 'fundamentacion', 'label': 'Fundamentación', 'type': 'textarea'}
            ]
        },
        'burofax': {
            'name': 'Burofax',
            'description': 'Comunicación certificada con valor probatorio',
            'fields': [
                {'name': 'remitente', 'label': 'Remitente', 'type': 'textarea'},
                {'name': 'destinatario', 'label': 'Destinatario', 'type': 'textarea'},
                {'name': 'asunto', 'label': 'Asunto', 'type': 'text'},
                {'name': 'contenido', 'label': 'Contenido', 'type': 'textarea'},
                {'name': 'requerimiento', 'label': 'Requerimiento', 'type': 'textarea'}
            ]
        }
    }
    return jsonify(templates)

from datetime import datetime

def open_browser():
    """Abrir navegador automáticamente"""
    webbrowser.open('http://localhost:5011')

if __name__ == '__main__':
    print("🚀 Iniciando LexDocsPro LITE v2.0...")
    print(f"📁 Directorio: {EXPEDIENTES_DIR}")
    print(f"📄 Documentos generados: {GENERATED_DOCS_DIR}")
    print("🌐 Abriendo navegador en http://localhost:5011")
    
    Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=5001, debug=True)

from services.lexnet_analyzer_v2 import LexNetAnalyzerV2 as LexNetAnalyzer

# Inicializar analizador
lexnet_analyzer = LexNetAnalyzer(ai_service)

@app.route('/api/lexnet/analyze', methods=['POST'])
def analyze_lexnet():
    """Analizar notificación LexNET"""
    try:
        data = request.json
        textos = data.get('textos', {})
        provider = data.get('provider', 'ollama')
        
        analisis = lexnet_analyzer.analizar_notificacion(textos, provider)
        
        # Guardar análisis
        filename = f"analisis_lexnet_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        file_path = GENERATED_DOCS_DIR / filename
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(analisis)
        
        return jsonify({
            'success': True,
            'analisis': analisis,
            'filename': filename,
            'path': str(file_path)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr/upload', methods=['POST'])
def ocr_upload():
    """OCR directo desde archivo subido"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'Empty filename'}), 400
        
        # Guardar temporalmente
        temp_path = EXPEDIENTES_DIR / '_temp' / file.filename
        temp_path.parent.mkdir(exist_ok=True)
        file.save(temp_path)
        
        # Extraer texto
        text = ocr_service.extract_text(temp_path)
        
        # Limpiar archivo temporal
        temp_path.unlink()
        
        return jsonify({
            'success': True,
            'text': text,
            'filename': file.filename
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ============================================
# ENDPOINTS ANALIZADOR LEXNET
# ============================================

@app.route('/api/ocr/upload', methods=['POST'])
def ocr_upload():
    """Extraer texto de archivo subido"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No se envió archivo'})
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'success': False, 'error': 'Nombre de archivo vacío'})
        
        # Guardar temporalmente
        temp_dir = tempfile.mkdtemp()
        temp_path = os.path.join(temp_dir, file.filename)
        file.save(temp_path)
        
        try:
            # Extraer texto con OCR
            text = ocr_service.extraer_texto(temp_path)
            
            return jsonify({
                'success': True,
                'text': text,
                'filename': file.filename
            })
            
        finally:
            # Limpiar archivos temporales
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
        print(f"📄 Archivos: {len(archivos)}")
        
        # Validar que haya al menos un texto
        if not any(textos.values()):
            return jsonify({
                'success': False,
                'error': 'No se pudo extraer texto de los archivos'
            })
        
        # Analizar con LexNET Analyzer
        from services.lexnet_analyzer import LexNetAnalyzer
        analyzer = LexNetAnalyzer()
        
        analisis = analyzer.analizar_notificacion(textos, provider)
        
        # Guardar en carpeta _GENERADOS
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

