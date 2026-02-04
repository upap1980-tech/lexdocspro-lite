# 🚀 LexDocsPro Enterprise v3.0 - SETUP COMPLETO

## **FASE 1: PREPARACIÓN DEL ENTORNO (5 minutos)**

### 1️⃣ Clonar/Preparar Proyecto
```bash
cd ~/Desktop
mkdir -p LEXDOCS_ENTERPRISE
cd LEXDOCS_ENTERPRISE

# Crear estructura
mkdir -p backend frontend services config
```

### 2️⃣ Instalar Dependencias Python

#### **Archivo: requirements.txt**
```
# Backend
Flask==3.0.0
Flask-CORS==4.0.0

# PDF & OCR
PyPDF2==3.0.1
pdf2image==1.16.3
pytesseract==0.3.10
Pillow>=10.2.0
PyMuPDF==1.23.8

# IA - Local
ollama==0.1.0

# IA - Cloud (Fallback)
groq==0.4.2
anthropic==0.18.0
openai==1.12.0
google-generativeai==0.3.2

# Utilidades
python-dotenv==1.0.0
requests==2.31.0
watchdog==3.0.0
```

```bash
pip install -r requirements.txt
```

### 3️⃣ Instalar Tesseract (OCR)

**macOS:**
```bash
brew install tesseract
```

**Windows:**
Descargar: https://github.com/UB-Mannheim/tesseract/wiki

**Linux:**
```bash
sudo apt-get install tesseract-ocr
```

### 4️⃣ Instalar Ollama (IA Local)
- Descargar: https://ollama.ai
- Instalar y ejecutar en terminal: `ollama run llama2`
- Verificar: `curl http://localhost:11434/api/tags`

---

## **FASE 2: CONFIGURACIÓN DEL BACKEND (10 minutos)**

### 1️⃣ Crear archivo `.env`
```bash
cat > .env << 'EOF'
# IA Configuration
DEFAULT_AI_PROVIDER=ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama2

# Cloud APIs (Opcional - para fallback)
GROQ_API_KEY=
PERPLEXITY_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=

# Directorios
BASE_DIR=~/Desktop/EXPEDIENTES_LEXDOCS
PENDING_DIR=~/Desktop/PENDIENTES_LEXDOCS

# Server
FLASK_ENV=development
FLASK_DEBUG=True
EOF
```

### 2️⃣ Crear estructura de servicios

#### **backend/services/ai_service.py**
```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class AIService:
    def __init__(self):
        self.ollama_url = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')
        self.ollama_model = os.getenv('OLLAMA_MODEL', 'llama2')
        
    def analizar_documento(self, texto, prompt_template):
        """Analizar con Ollama Local"""
        try:
            response = requests.post(
                f'{self.ollama_url}/api/generate',
                json={
                    'model': self.ollama_model,
                    'prompt': f"{prompt_template}\n\n{texto}",
                    'stream': False,
                    'options': {'temperature': 0.1}
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json().get('response')
            return None
        except Exception as e:
            print(f"❌ Error Ollama: {e}")
            return None
    
    def get_available_providers(self):
        return ['ollama', 'groq', 'perplexity', 'openai']
```

#### **backend/services/ocr_service.py**
```python
import pytesseract
from pdf2image import convert_from_path
import fitz

class OCRService:
    def extraer_texto(self, ruta_pdf):
        """Extraer texto de PDF"""
        try:
            # Intentar con PyMuPDF primero (más rápido)
            doc = fitz.open(ruta_pdf)
            texto = ""
            for page in doc:
                texto += page.get_text()
            doc.close()
            
            if texto.strip():
                return texto
            
            # Fallback a Tesseract si PyMuPDF no funciona
            imagenes = convert_from_path(ruta_pdf)
            texto_ocr = ""
            for imagen in imagenes:
                texto_ocr += pytesseract.image_to_string(imagen, lang='spa')
            return texto_ocr
        except Exception as e:
            print(f"❌ Error OCR: {e}")
            return ""
```

#### **backend/services/db_service.py**
```python
import sqlite3
from datetime import datetime

class DatabaseService:
    def __init__(self, db_path='lexdocs.db'):
        self.db_path = db_path
        self.init_db()
    
    def init_db(self):
        """Inicializar base de datos"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS documentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                archivo_original TEXT NOT NULL,
                cliente_detectado TEXT,
                tipo_documento TEXT,
                fecha_documento TEXT,
                fecha_procesamiento TEXT,
                estado TEXT,
                confianza_ia REAL,
                ruta_definitiva TEXT,
                timestamp TEXT
            )
        """)
        
        cur.execute("""
            CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                nivel TEXT,
                origen TEXT,
                mensaje TEXT,
                documento_id INTEGER
            )
        """)
        
        conn.commit()
        conn.close()
    
    def guardar_documento(self, archivo, metadata, estado, confianza):
        """Guardar documento en BD"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        
        cur.execute("""
            INSERT INTO documentos (
                archivo_original, cliente_detectado, tipo_documento,
                fecha_documento, estado, confianza_ia, timestamp,
                fecha_procesamiento
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            archivo,
            metadata.get('nombre_cliente'),
            metadata.get('tipo_documento'),
            metadata.get('fecha_documento'),
            estado,
            confianza,
            datetime.now().isoformat(),
            datetime.now().strftime('%Y%m%d')
        ))
        
        doc_id = cur.lastrowid
        conn.commit()
        conn.close()
        return doc_id
    
    def obtener_estadisticas_hoy(self):
        """Obtener stats del día"""
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        hoy = datetime.now().strftime('%Y%m%d')
        
        cur.execute("""
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN estado = 'aprobado' THEN 1 ELSE 0 END) as automaticos,
                SUM(CASE WHEN estado = 'revision' THEN 1 ELSE 0 END) as en_revision,
                SUM(CASE WHEN estado = 'error' THEN 1 ELSE 0 END) as errores
            FROM documentos
            WHERE fecha_procesamiento = ?
        """, (hoy,))
        
        resultado = cur.fetchone()
        conn.close()
        
        return {
            'total_hoy': resultado[0] or 0,
            'automaticos': resultado[1] or 0,
            'en_revision': resultado[2] or 0,
            'errores': resultado[3] or 0,
            'porcentaje_auto': 0
        }
```

### 3️⃣ Backend Principal (`run.py`)

```python
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS
import os
from dotenv import load_dotenv
from services.ai_service import AIService
from services.ocr_service import OCRService
from services.db_service import DatabaseService

load_dotenv()

app = Flask(__name__)
CORS(app)

# Servicios
ai_service = AIService()
ocr_service = OCRService()
db_service = DatabaseService()

# Configuración
BASE_DIR = os.path.expanduser(os.getenv('BASE_DIR', '~/Desktop/EXPEDIENTES_LEXDOCS'))
PENDING_DIR = os.path.expanduser(os.getenv('PENDING_DIR', '~/Desktop/PENDIENTES_LEXDOCS'))

os.makedirs(BASE_DIR, exist_ok=True)
os.makedirs(PENDING_DIR, exist_ok=True)

# ═══════════════════════════════════════════════════════════
# RUTAS
# ═══════════════════════════════════════════════════════════

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/health')
def health():
    return jsonify({'status': 'ok', 'version': '3.0'})

@app.route('/api/autoprocesador/stats')
def get_stats():
    stats = db_service.obtener_estadisticas_hoy()
    return jsonify({'success': True, 'stats': stats})

@app.route('/api/document/smart-analyze', methods=['POST'])
def smart_analyze():
    """Análisis inteligente con IA"""
    try:
        file = request.files.get('file')
        if not file:
            return jsonify({'error': 'No file provided'}), 400
        
        # Guardar temporalmente
        import tempfile
        tmpdir = tempfile.mkdtemp()
        tmppath = os.path.join(tmpdir, file.filename)
        file.save(tmppath)
        
        # Extraer texto
        texto = ocr_service.extraer_texto(tmppath)
        
        # Analizar con IA
        prompt = """
        Analiza este documento judicial español.
        Extrae SOLO un JSON válido con:
        - nombre_cliente: nombre completo (NO abogados)
        - tipo_documento: notificacion_lexnet, auto, sentencia, demanda
        - fecha_documento: formato dd/mm/aaaa
        - confianza: alta, media, baja
        
        DOCUMENTO:
        """ + texto[:5000]
        
        respuesta_ia = ai_service.analizar_documento(texto, prompt)
        
        # Parsear respuesta
        import json
        import re
        
        metadata = {
            'nombre_cliente': 'DESCONOCIDO',
            'tipo_documento': 'documento',
            'fecha_documento': '',
            'confianza': 'baja',
            'ano': str(datetime.now().year)
        }
        
        if respuesta_ia:
            try:
                json_match = re.search(r'\{[^{}]*\}', respuesta_ia, re.DOTALL)
                if json_match:
                    metadata.update(json.loads(json_match.group()))
            except:
                pass
        
        return jsonify({
            'success': True,
            'temp_file_path': tmppath,
            'metadata': metadata,
            'cliente_propuesto': {
                'codigo': '2026-01',
                'nombre': metadata['nombre_cliente'],
                'carpeta': f"2026-01 {metadata['nombre_cliente']}"
            },
            'ruta_completa': f"{BASE_DIR}/2026/2026-01 {metadata['nombre_cliente']}/{file.filename}"
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/autoprocesador/cola-revision')
def get_review_queue():
    conn = sqlite3.connect('lexdocs.db')
    cur = conn.cursor()
    cur.execute("SELECT * FROM documentos WHERE estado = 'revision' LIMIT 20")
    rows = cur.fetchall()
    conn.close()
    
    documentos = [
        {
            'id': r[0],
            'archivo_original': r[1],
            'cliente_detectado': r[2],
            'tipo_documento': r[3],
            'confianza_ia': r[7] or 0.65
        }
        for r in rows
    ]
    
    return jsonify({'success': True, 'documentos': documentos})

@app.route('/api/autoprocesador/procesados-hoy')
def get_processed():
    conn = sqlite3.connect('lexdocs.db')
    cur = conn.cursor()
    hoy = datetime.now().strftime('%Y%m%d')
    cur.execute("""
        SELECT * FROM documentos 
        WHERE estado = 'aprobado' AND fecha_procesamiento = ?
        LIMIT 50
    """, (hoy,))
    rows = cur.fetchall()
    conn.close()
    
    documentos = [
        {
            'id': r[0],
            'archivo_original': r[1],
            'cliente_detectado': r[2],
            'tipo_documento': r[3],
            'fecha_documento': r[4],
            'ruta_definitiva': r[8] or 'N/A'
        }
        for r in rows
    ]
    
    return jsonify({'success': True, 'documentos': documentos})

@app.route('/api/document/save-organized', methods=['POST'])
def save_organized():
    """Guardar documento en carpeta estructurada"""
    try:
        data = request.json
        temp_path = data.get('temp_file_path')
        dest_path = data.get('dest_path')
        
        import shutil
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.move(temp_path, dest_path)
        
        return jsonify({'success': True, 'saved_path': dest_path})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# ═══════════════════════════════════════════════════════════
# INIT
# ═══════════════════════════════════════════════════════════

if __name__ == '__main__':
    print("🚀 LexDocsPro Enterprise v3.0")
    print(f"📁 Base: {BASE_DIR}")
    app.run(debug=True, host='0.0.0.0', port=5001)
```

---

## **FASE 3: SETUP DIRECTORIOS (2 minutos)**

```bash
# Crear estructura
mkdir -p ~/Desktop/EXPEDIENTES_LEXDOCS/2026
mkdir -p ~/Desktop/PENDIENTES_LEXDOCS
mkdir -p ~/Desktop/PENDIENTES_LEXDOCS/REVISAR_MANUAL

echo "✅ Estructura creada"
```

---

## **FASE 4: EJECUCIÓN**

### **Terminal 1: Iniciar Ollama (si no está corriendo)**
```bash
ollama run llama2
# O si ya está: ollama serve
```

### **Terminal 2: Iniciar Backend**
```bash
cd ~/Desktop/LEXDOCS_ENTERPRISE
python run.py
```

### **Terminal 3: Abrir Frontend**
```bash
# Automáticamente en navegador:
# http://localhost:5001
```

---

## **VERIFICACIÓN RÁPIDA**

✅ Backend activo: `curl http://localhost:5001/api/health`
✅ Ollama activo: `curl http://localhost:11434/api/tags`
✅ Frontend: `http://localhost:5001`

---

## **FLUJO DE USO**

1. **Arrastra PDF** → Panel "Subir & Clasificar"
2. **IA analiza** → Extrae cliente, tipo, fecha
3. **Confianza alta?** → ✅ Guardar automáticamente
4. **Confianza media?** → ✏️ Revisar y Editar
5. **Documento guardado** → Aparece en "Procesados Hoy"

---

## **TROUBLESHOOTING**

| Error | Solución |
|-------|----------|
| `ConnectionError: Ollama` | Ejecutar `ollama serve` en otra terminal |
| `Module not found` | Ejecutar `pip install -r requirements.txt` |
| `PORT 5001 in use` | `lsof -i :5001` y matar proceso |
| `Permission denied` | `chmod +x *.py` |

---

## **OPTIMIZACIONES SIGUIENTES**

1. **Procesador en background** → `auto_procesar.py` (monitorear PENDIENTES_LEXDOCS)
2. **Integración WebSocket** → Stats en vivo
3. **Base de datos mejorada** → PostgreSQL
4. **Docker** → Deploy en producción

