#!/bin/bash

# Script de instalación completo para LexDocsPro LITE v2.0
# Instala dependencias de sistema y Python

echo "============================================"
echo "🚀 Instalación de LexDocsPro LITE v2.0"
echo "============================================"

# Detectar si estamos en macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "⚠️ Este script está optimizado para macOS"
    echo "Para Linux, adapta los comandos de Homebrew a apt/yum"
    exit 1
fi

# 1. Instalar Homebrew si no está instalado
if ! command -v brew &> /dev/null; then
    echo "📦 Instalando Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
else
    echo "✅ Homebrew ya instalado"
fi

# 2. Instalar dependencias de sistema
echo ""
echo "📦 Instalando dependencias de sistema..."

# Tesseract OCR (para extracción de texto de imágenes)
if ! command -v tesseract &> /dev/null; then
    echo "Installing Tesseract OCR..."
    brew install tesseract tesseract-lang
else
    echo "✅ Tesseract ya instalado"
fi

# Poppler (para pdf2image)
if ! brew list poppler &> /dev/null; then
    echo "Installing Poppler..."
    brew install poppler
else
    echo "✅ Poppler ya instalado"
fi

# Ghostscript (para procesamiento avanzado de PDFs)
if ! brew list ghostscript &> /dev/null; then
    echo "Installing Ghostscript..."
    brew install ghostscript
else
    echo "✅ Ghostscript ya instalado"
fi

# 3. Verificar Python
echo ""
echo "🐍 Verificando Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 no encontrado"
    echo "Instalando Python 3..."
    brew install python@3.11
else
    python_version=$(python3 --version)
    echo "✅ $python_version"
fi

# 4. Crear entorno virtual si no existe
echo ""
echo "📦 Configurando entorno virtual..."

if [ ! -d ".venv" ]; then
    echo "Creando entorno virtual..."
    python3 -m venv .venv
else
    echo "✅ Entorno virtual ya existe"
fi

# 5. Activar entorno virtual
echo "Activando entorno virtual..."
source .venv/bin/activate

# 6. Actualizar pip
echo ""
echo "📦 Actualizando pip..."
pip install --upgrade pip

# 7. Instalar dependencias de Python
echo ""
echo "📦 Instalando dependencias de Python..."
pip install -r requirements.txt

# 8. Verificar instalación
echo ""
echo "============================================"
echo "✅ Verificando instalación"
echo "============================================"

# Verificar Tesseract
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version | head -n 1)
    echo "✅ $tesseract_version"
else
    echo "❌ Tesseract no instalado correctamente"
fi

# Verificar Python packages críticos
echo ""
echo "📦 Verificando paquetes Python..."
python3 << EOF
import sys
packages = [
    'flask',
    'flask_jwt_extended',
    'bcrypt',
    'pytesseract',
    'pdf2image',
    'pymupdf',
    'watchdog',
    'PIL'
]

missing = []
for pkg in packages:
    try:
        __import__(pkg)
        print(f"✅ {pkg}")
    except ImportError:
        print(f"❌ {pkg} - NO ENCONTRADO")
        missing.append(pkg)

if missing:
    print(f"\n⚠️ Paquetes faltantes: {', '.join(missing)}")
    sys.exit(1)
EOF

# 9. Crear carpetas necesarias
echo ""
echo "📁 Creando carpetas del proyecto..."
mkdir -p ~/Desktop/EXPEDIENTES
mkdir -p ~/Desktop/EXPEDIENTES/_GENERADOS
mkdir -p ~/Desktop/PENDIENTES_LEXDOCS

echo "✅ Carpetas creadas:"
echo "   ~/Desktop/EXPEDIENTES"
echo "   ~/Desktop/EXPEDIENTES/_GENERADOS"
echo "   ~/Desktop/PENDIENTES_LEXDOCS"

# 10. Configurar .env si no existe
if [ ! -f ".env" ]; then
    echo ""
    echo "📝 Configurando archivo .env..."
    cp .env.example .env
    
    # Generar JWT secret
    jwt_secret=$(openssl rand -hex 32)
    
    # Reemplazar en .env (macOS requiere -i '')
    sed -i '' "s/JWT_SECRET_KEY=CAMBIAR_ESTO_POR_STRING_ALEATORIO_32_CHARS/JWT_SECRET_KEY=$jwt_secret/" .env
    
    echo "✅ Archivo .env creado con JWT_SECRET_KEY generado"
else
    echo "✅ Archivo .env ya existe"
fi

# Finalización
echo ""
echo "============================================"
echo "✅ INSTALACIÓN COMPLETADA"
echo "============================================"
echo ""
echo "Próximos pasos:"
echo ""
echo "1. Crear usuario administrador:"
echo "   python create_admin.py"
echo ""
echo "2. Iniciar aplicación:"
echo "   python run.py"
echo ""
echo "3. Abrir navegador:"
echo "   http://localhost:5002"
echo ""
echo "============================================"
