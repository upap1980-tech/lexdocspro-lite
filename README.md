# 📚 LexDocsPro LITE v2.0

Sistema integral de gestión de documentos legales con IA multi-proveedor, generación automática de documentos y analizador de notificaciones LexNET.

## 🎯 Características Principales

### 1. 💬 Consultas Inteligentes
- Explorador de expedientes con navegación por carpetas
- Visor de PDFs integrado
- OCR automático para extracción de texto
- Chat con múltiples proveedores de IA:
  - 🏠 Ollama (local)
  - ⚡ Groq
  - 🤖 OpenAI (ChatGPT)
  - 🔍 Perplexity
  - 💎 Gemini
  - 🌊 DeepSeek
- Modos de consulta:
  - ⚡ Consulta Rápida
  - 🔍 Análisis Profundo
  - 📚 Investigación

### 2. 📝 Generador de Documentos
Generación profesional de documentos legales usando IA:
- **Demanda Civil**: Formulario completo con partes, hechos, petitorio
- **Escrito de Alegaciones**: Respuestas estructuradas
- **Recurso de Apelación**: Fundamentos y súplica
- **Burofax**: Notificaciones formales
- **Requerimiento Extrajudicial**: Comunicaciones previas

Todos los documentos se generan con formato profesional y se guardan automáticamente.

### 3. ⚖️ Analizador LexNET
Sistema inteligente para análisis de notificaciones judiciales:

**Características:**
- Subida múltiple de archivos (PDFs, imágenes, Word, Excel)
- Clasificación automática: RESUMEN, CARÁTULA, Resoluciones, Adjuntos
- Extracción de texto con OCR avanzado
- Análisis estructurado con IA que incluye:
  - Datos del procedimiento
  - Tipo de resolución
  - Órgano judicial
  - Partes procesales
  - Hechos relevantes
  - Fundamentación jurídica
  - **Cálculo automático de plazos**
  - Acciones recomendadas
  - Riesgos y consecuencias

**Cálculo de Plazos:**
- Detección automática de plazos en resoluciones
- Cálculo de fecha límite con días hábiles
- Identificación del tipo de plazo (recursos, alegaciones, etc.)
- Alertas de urgencia

## 🚀 Instalación

### Requisitos Previos
- Python 3.8+
- Tesseract OCR instalado en el sistema
- Ollama (para IA local) u otras APIs configuradas

### Instalación

```bash
# 1. Clonar o descargar el proyecto
cd ~/Desktop/PROYECTOS
git clone [URL] LexDocsPro-LITE
cd LexDocsPro-LITE

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar Tesseract OCR
# macOS:
brew install tesseract tesseract-lang

# Ubuntu/Debian:
sudo apt-get install tesseract-ocr tesseract-ocr-spa

# Windows:
# Descargar de: https://github.com/UB-Mannheim/tesseract/wiki

# 5. Configurar (opcional)
# Editar config.py para ajustar rutas y API keys

Configuración
Edita config.py para personalizar:
# Directorio base de expedientes
BASE_DIR = "~/Desktop/EXPEDIENTES"

# API Keys (opcional, para proveedores cloud)
OPENAI_API_KEY = "tu-api-key"
GROQ_API_KEY = "tu-api-key"
PERPLEXITY_API_KEY = "tu-api-key"

📖 Uso
Iniciar el servidor
cd ~/Desktop/PROYECTOS/LexDocsPro-LITE
source venv/bin/activate
python run.py

El navegador se abrirá automáticamente en http://localhost:5001
Estructura de Carpetas
~/Desktop/EXPEDIENTES/
├── 2024/
│   ├── CLIENTE_A/
│   │   ├── documento1.pdf
│   │   └── documento2.pdf
│   └── CLIENTE_B/
└── _GENERADOS/          # Documentos generados automáticamente
    ├── demanda_civil_20260131_120000.txt
    └── ANALISIS_LEXNET_20260131_150000.txt

Flujo de Trabajo
1. Consultar Documentos
Navega por las carpetas de expedientes

Selecciona un PDF

Click en "Ejecutar OCR"

Escribe tu consulta en el chat

Selecciona proveedor de IA y modo

Recibe respuesta inteligente
2. Generar Documentos
Pestaña "Generar Documentos"

Selecciona tipo de documento

Rellena los campos del formulario

Click en "Generar Documento"

Copia o descarga el resultado


3. Analizar Notificaciones LexNET
Pestaña "Analizador LexNET"

Sube uno o más archivos (RESUMEN.pdf, CARATULA.pdf, resolución, etc.)

Click en "Analizar Notificación"

Espera el análisis completo (incluye cálculo de plazos)

Copia, descarga o exporta el análisis
🏗️ Arquitectura
LexDocsPro-LITE/
├── run.py                 # Servidor Flask principal
├── config.py              # Configuración
├── requirements.txt       # Dependencias Python
├── services/
│   ├── ai_service.py      # Gestor de múltiples IAs
│   ├── ocr_service.py     # Extracción de texto (OCR)
│   ├── document_generator.py  # Generación de documentos
│   ├── lexnet_analyzer.py     # Análisis de notificaciones
│   └── ollama_service.py      # Cliente Ollama
├── templates/
│   └── index.html         # Interfaz web única
└── static/
    ├── css/
    │   └── style.css      # Estilos
    └── js/
        └── app.js         # Lógica frontend

🔧 Tecnologías

Backend
Flask: Servidor web

PyMuPDF: Extracción rápida de texto de PDFs

Tesseract OCR: OCR para PDFs escaneados

pdf2image: Conversión PDF a imagen

Ollama: IA local (LLaMA, Mistral, etc.)

Frontend
HTML5/CSS3: Interfaz moderna

JavaScript Vanilla: Sin frameworks pesados

Diseño responsive: Adaptable a móviles

IA Multi-Proveedor
Ollama (local)

OpenAI GPT-4

Groq (ultrarrápido)

Perplexity

Google Gemini

DeepSeek
📊 Casos de Uso
1. Abogado Procesalista
Recibe notificación LexNET

Sube los 3 PDFs al analizador

Obtiene análisis completo con plazos calculados

Genera escrito de alegaciones con el generador

Todo en menos de 5 minutos

2. Despacho Pequeño
Organiza expedientes por año/cliente

Consulta documentos antiguos sin leerlos completos

La IA resume y responde preguntas específicas

Genera documentos estándar automáticamente

3. Estudiante de Derecho
Analiza sentencias y resoluciones

Extrae jurisprudencia relevante

Genera borradores de escritos

Practica con casos reales
🔐 Seguridad y Privacidad
Datos locales: Los expedientes nunca salen de tu ordenador

Ollama local: IA sin enviar datos a internet

APIs opcionales: Usa cloud solo si quieres

Sin almacenamiento: No se guardan conversaciones


🐛 Solución de Problemas
OCR no funciona
# Verificar instalación de Tesseract
tesseract --version

# Reinstalar idioma español
# macOS:
brew reinstall tesseract tesseract-lang

# Linux:
sudo apt-get install --reinstall tesseract-ocr-spa

Ollama no responde
# Verificar que Ollama está corriendo
ollama list

# Iniciar Ollama si no está activo
ollama serve

# Descargar un modelo
ollama pull llama3.2

Puerto 5001 ocupado
Edita run.py y cambia el puerto:
app.run(debug=True, host='0.0.0.0', port=5002)

📝 Roadmap
v2.1 (Próximamente)
 Exportación directa a iCloud

 Integración con calendarios para alertas de plazos

 Soporte para más tipos de documentos

 Búsqueda global por contenido
v3.0 (Futuro)
 Aplicación móvil (iOS/Android)

 Base de datos para jurisprudencia

 Sistema de alertas automáticas

 Análisis predictivo con ML
👥 Contribuciones
Las contribuciones son bienvenidas. Por favor:

Fork el proyecto

Crea una rama para tu feature

Commit tus cambios

Push a la rama

Abre un Pull Request
📄 Licencia
Este proyecto es privado y de uso personal/profesional.
🙏 Agradecimientos
Ollama por la IA local

Tesseract por el OCR

Comunidad de código abierto
📧 Contacto
Para soporte o consultas: [Tu email/contacto]
Desarrollado con ❤️ para facilitar el trabajo legal

Versión 2.0 - Enero 2026
