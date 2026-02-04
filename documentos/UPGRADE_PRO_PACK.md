# 📦 **LEXDOCSPRO LITE v3.0 PRO - UPGRADE PACK**

## 🎯 **QUÉ SE INSTALA:**

### ✅ **Backend Avanzado (run_pro.py)**
- Multi-modelo AI (Ollama, Groq, OpenAI)
- 12 generadores de documentos legales
- Analizador LexNET con cálculo de plazos
- OCR integrado (Tesseract)
- Export a iCloud
- Chat contextual
- Dashboard analytics
- Búsqueda semántica

### ✅ **Frontend Profesional**
- Interfaz moderna con Tailwind CSS
- 8 secciones principales
- Responsive design
- Dark/Light mode
- Charts y gráficos
- Gestor de expedientes

### ✅ **Documentos Generables (12 tipos)**
1. Demanda Civil
2. Contestación a Demanda
3. Recurso de Apelación
4. Demanda Penal
5. Solicitud Medida Cautelar
6. Recurso de Amparo
7. Demanda Laboral
8. Demanda Administrativa
9. Contrato de Servicios
10. Poder Notarial
11. Acta de Junta
12. Cláusulas Personalizadas

### ✅ **Funciones Avanzadas**
- Cálculo automático de plazos (Art. 131 LEC)
- Análisis de partes demandantes
- Extracción de jurisdicción
- Número de procedimiento automático
- Medidas cautelares detectadas
- Próximos pasos recomendados

---

## 📥 **INSTALACIÓN PASO A PASO:**

### 1️⃣ Descarga los archivos:
```bash
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE
```

### 2️⃣ Actualiza requirements.txt
```bash
pip install python-dotenv requests pytesseract pdf2image pillow groq openai
```

### 3️⃣ Reemplaza run.py con run_pro.py
```bash
cp run_pro.py run.py
```

### 4️⃣ Actualiza HTML/JS
```bash
cp index_pro.html templates/index.html
cp app_pro.js static/js/app.js
```

### 5️⃣ Reinicia servidor
```bash
source venv/bin/activate
python run.py
```

### 6️⃣ Abre navegador
```
http://localhost:5001
```

---

## 🔌 **CONFIGURAR MÚLTIPLES MODELOS:**

### Ollama (Local - YA TIENES)
```bash
ollama serve
# En otra terminal:
ollama pull lexdocs-legal-pro:latest
```

### Groq (Alternativa rápida - GRATIS)
1. Regístrate: https://console.groq.com
2. Copia API KEY
3. Añade a .env:
```
GROQ_API_KEY=tu_key_aqui
```

### OpenAI (Profesional - De pago)
1. Regístrate: https://platform.openai.com
2. Copia API KEY
3. Añade a .env:
```
OPENAI_API_KEY=tu_key_aqui
```

---

## 📊 **FUNCIONALIDADES PRINCIPALES:**

### 🎨 **UI/UX**
- Header con branding
- Sidebar de navegación
- 8 secciones
- Selector de modelos
- Status bar en tiempo real

### 📄 **Generador de Documentos**
- 12 tipos de documentos
- Plantillas inteligentes
- Exportar a TXT/PDF
- Edición en vivo

### 🔍 **Analizador LexNET**
- Upload de PDFs/TXT
- OCR automático
- Extracción de datos
- Cálculo de plazos
- Alertas automáticas

### 💬 **Chat Inteligente**
- Multi-modelo (cambiar en tiempo real)
- Contexto legal español
- Historial conversacional
- Respuestas formateadas

### 📚 **Gestor de Expedientes**
- CRUD completo
- Búsqueda avanzada
- Filtros por tipo/estado
- Export a iCloud

### 📈 **Dashboard**
- Estadísticas de documentos
- Gráficos de actividad
- Modelos más usados
- Últimas consultas

### 🔐 **Seguridad**
- Validación de inputs
- CORS configurado
- Error handling robusto
- Logging de operaciones

---

## 🎓 **TUTORIAL RÁPIDO:**

### Generar documento:
1. Click en "📄 Generador"
2. Selecciona tipo (ej: "Demanda Civil")
3. Escribe descripción del caso
4. Click "⚡ Generar"
5. Click "📋 Copiar" o "💾 Descargar"

### Analizar LexNET:
1. Click en "📋 LexNET"
2. Upload PDF del juzgado
3. Click "🔍 Analizar"
4. Recibe:
   - Partes
   - Plazos (con colores de urgencia)
   - Próximos pasos

### Chat legal:
1. Click en "💬 Chat"
2. Selecciona modelo (Ollama/Groq/OpenAI)
3. Escribe consulta legal
4. Recibe respuesta contextualizada

---

## 🔧 **TROUBLESHOOTING:**

**P: ¿Ollama no responde?**
```bash
ollama serve  # En otra terminal
```

**P: ¿Groq lento?**
- Usa Ollama local (más rápido en tu máquina)

**P: ¿PDF no se lee?**
```bash
brew install tesseract  # Instala OCR
```

**P: ¿CORS error?**
- Backend ya tiene CORS configurado

**P: ¿Puerto 5001 en uso?**
```bash
lsof -i :5001  # Ver qué lo usa
kill -9 <PID>  # Matar proceso
```

---

## 📞 **SOPORTE:**

Si algo falla:
1. Verifica que Ollama esté corriendo
2. Check `http://localhost:5001/api/chat` devuelve error
3. Revisa terminal del servidor por errores
4. Limpia cache del navegador (Cmd+Shift+R)

---

**¡LISTO PARA INSTALAR!** 🚀

Copia los 3 archivos (run_pro.py, index_pro.html, app_pro.js) en el proyecto y ejecuta el setup.
