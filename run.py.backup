#!/usr/bin/env python3
from flask import Flask, render_template, request, jsonify, send_file
from flask_cors import CORS
import os
from pathlib import Path
import webbrowser
from threading import Timer

from services.file_service import FileService
from services.ocr_service import OCRService
from services.ollama_service import OllamaService

BASE_DIR = Path(__file__).parent
EXPEDIENTES_DIR = Path.home() / "Desktop" / "EXPEDIENTES"
EXPEDIENTES_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
CORS(app)

file_service = FileService(EXPEDIENTES_DIR)
ocr_service = OCRService()
ollama_service = OllamaService()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        path = request.args.get('path', '')
        files = file_service.list_directory(path)
        return jsonify(files)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/pdf/<path:filename>')
def serve_pdf(filename):
    try:
        file_path = EXPEDIENTES_DIR / filename
        if file_path.exists() and file_path.suffix.lower() == '.pdf':
            return send_file(file_path, mimetype='application/pdf')
        return jsonify({'error': 'Archivo no encontrado'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ocr', methods=['POST'])
def extract_text():
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
    try:
        data = request.json
        prompt = data.get('prompt')
        context = data.get('context', '')
        
        response = ollama_service.chat(prompt, context)
        return jsonify({'response': response})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def open_browser():
    webbrowser.open('http://localhost:5001')

if __name__ == '__main__':
    print("🚀 Iniciando LexDocsPro LITE...")
    print(f"📁 Directorio: {EXPEDIENTES_DIR}")
    print("🌐 Abriendo navegador en http://localhost:5001")
    
    Timer(1, open_browser).start()
    app.run(host='0.0.0.0', port=5001, debug=True)
