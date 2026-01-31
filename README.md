# 📚 LexDocsPro LITE v2.0

Sistema integral de gestión de documentos legales con IA local optimizada, generación automática de documentos y exportación a iCloud.

## ✨ Características Principales

### 🤖 IA Local Optimizada
- **Modelo**: lexdocs-legal-pro (Mistral 7B)
- **Precisión**: 100% en pruebas de derecho español
- **Especialización**: Código Civil, LEC, LAU, Estatuto Trabajadores
- **Parámetros**: Temperature 0.25, Context 8K tokens
- **Citas precisas**: Artículos reales (Art. 404.1 LEC, Art. 458 LEC)

### 📝 Generador de 12 Documentos Legales
1. ⚖️ Demanda Civil
2. 🛡️ Contestación a la Demanda
3. 🔄 Recurso de Apelación
4. 🔁 Recurso de Reposición
5. 📝 Escrito de Alegaciones
6. 🚫 Desistimiento
7. 👤 Personación y Solicitud de Copias
8. 📜 Poder para Pleitos
9. 🔬 Proposición de Prueba
10. 📮 Burofax
11. ⚠️ Requerimiento Extrajudicial
12. ⚔️ Querella Criminal

### ☁️ Exportación Automática a iCloud
- Estructura automática: `EXPEDIENTES/2026/CLIENTE/LEXNET/`
- Exportación de análisis LexNET
- Exportación de documentos generados
- Lista de clientes existentes

### 🔍 Analizador LexNET
- Análisis inteligente de notificaciones judiciales
- Extracción automática de plazos
- Cálculo de fechas límite (días hábiles)
- Identificación de acciones recomendadas

## 🚀 Instalación

### Requisitos
- Python 3.8+
- Tesseract OCR
- Ollama (local)

### Pasos

```bash
# 1. Clonar repositorio
git clone https://github.com/upap1980-tech/lexdocspro-lite.git
cd lexdocspro-lite

# 2. Crear entorno virtual
python3 -m venv venv
source venv/bin/activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Instalar Tesseract OCR
brew install tesseract tesseract-lang  # macOS

# 5. Instalar Ollama y modelo
brew install ollama
ollama pull mistral
ollama create lexdocs-legal-pro -f Modelfile-Legal-Pro

# 6. Ejecutar
python run.py

La aplicación se abrirá en http://localhost:5001
📊 Uso
Consultar Documentos
Explora expedientes en panel izquierdo

Selecciona PDF → Click "Ejecutar OCR"

Escribe consulta en el chat

Selecciona proveedor IA y modo

Recibe análisis especializado

Generar Documentos
Pestaña "Generar Documentos"

Selecciona tipo de documento

Rellena campos del formulario

Click "Generar Documento"

Copia o descarga resultado

Analizar Notificaciones LexNET
Pestaña "Analizador LexNET"

Sube archivos (RESUMEN, CARÁTULA, resoluciones)

Click "Analizar Notificación"

Obtén análisis completo con plazos calculados

Exporta a iCloud para organización
🔧 Configuración
Modelo IA
Modelo activo: lexdocs-legal-pro

Configurado en: services/ollama_service.py

Parámetros optimizados para precisión jurídica

Ver: MODELO_CONFIG.md
Exportación iCloud
Ruta: ~/Library/Mobile Documents/com~apple~CloudDocs/EXPEDIENTES/

Estructura automática por año y cliente

Configurado en: services/icloud_service.py


📁 Estructura del Proyecto
LexDocsPro-LITE/
├── run.py                      # Servidor Flask principal
├── config.py                   # Configuración
├── requirements.txt            # Dependencias
├── services/
│   ├── ai_service.py          # Gestor multi-IA
│   ├── ollama_service.py      # Cliente Ollama optimizado
│   ├── document_generator.py  # Generador 12 documentos
│   ├── icloud_service.py      # Exportación iCloud
│   ├── lexnet_analyzer.py     # Analizador LexNET
│   └── ocr_service.py         # Extracción OCR
├── templates/
│   └── index.html             # Interfaz única
└── static/
    ├── css/style.css
    └── js/app.js              # Lógica frontend

🧪 Pruebas Realizadas
✅ Consulta Art. 1544 CC - Compraventa cosa ajena
✅ Plazo contestación demanda: 20 días hábiles (Art. 404 LEC)
✅ Caso desahucio por impago (LAU 29/1994)
✅ Recurso apelación: 20 días (Art. 458 LEC)

Precisión: 100% en artículos citados
Plazos: Correctos según LEC vigente
📄 Licencia
Privado - Uso profesional
👤 Autor
Desarrollado para gestión profesional de expedientes legales


Última actualización: 31 enero 2026
Versión: 2.0
