#!/bin/bash

echo "=============================================="
echo "🔍 DIAGNÓSTICO LexDocsPro LITE v2.0"
echo "=============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 1. VERIFICAR PYTHON
echo "1️⃣  Verificando Python..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    echo -e "${GREEN}✅ Python instalado: $PYTHON_VERSION${NC}"
else
    echo -e "${RED}❌ Python3 no encontrado${NC}"
    exit 1
fi

# 2. VERIFICAR ENTORNO VIRTUAL
echo ""
echo "2️⃣  Verificando entorno virtual..."
if [ -d "venv" ]; then
    echo -e "${GREEN}✅ Entorno virtual existe${NC}"
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual activado${NC}"
else
    echo -e "${YELLOW}⚠️  Creando entorno virtual...${NC}"
    python3 -m venv venv
    source venv/bin/activate
    echo -e "${GREEN}✅ Entorno virtual creado y activado${NC}"
fi

# 3. VERIFICAR E INSTALAR DEPENDENCIAS
echo ""
echo "3️⃣  Verificando dependencias..."
pip install --upgrade pip > /dev/null 2>&1

echo "   Instalando dependencias desde requirements.txt..."
pip install -r requirements.txt > /dev/null 2>&1

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ Todas las dependencias instaladas${NC}"
else
    echo -e "${RED}❌ Error instalando dependencias${NC}"
    pip install -r requirements.txt
    exit 1
fi

# 4. VERIFICAR TESSERACT OCR
echo ""
echo "4️⃣  Verificando Tesseract OCR..."
if command -v tesseract &> /dev/null; then
    TESSERACT_VERSION=$(tesseract --version 2>&1 | head -1)
    echo -e "${GREEN}✅ Tesseract instalado: $TESSERACT_VERSION${NC}"
else
    echo -e "${YELLOW}⚠️  Tesseract no encontrado${NC}"
    echo "   Instalando con Homebrew..."
    brew install tesseract tesseract-lang
fi

# 5. VERIFICAR OLLAMA
echo ""
echo "5️⃣  Verificando Ollama..."
if command -v ollama &> /dev/null; then
    echo -e "${GREEN}✅ Ollama instalado${NC}"
    
    # Verificar si Ollama está corriendo
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}✅ Ollama está corriendo${NC}"
        
        # Verificar modelo optimizado
        if ollama list | grep -q "lexdocs-legal-pro"; then
            echo -e "${GREEN}✅ Modelo lexdocs-legal-pro disponible${NC}"
        else
            echo -e "${YELLOW}⚠️  Modelo lexdocs-legal-pro no encontrado${NC}"
            echo "   Puedes crearlo después con: ollama create lexdocs-legal-pro -f Modelfile-Legal-Pro"
        fi
    else
        echo -e "${YELLOW}⚠️  Ollama no está corriendo. Iniciando...${NC}"
        ollama serve > /dev/null 2>&1 &
        sleep 3
        echo -e "${GREEN}✅ Ollama iniciado${NC}"
    fi
else
    echo -e "${YELLOW}⚠️  Ollama no instalado (opcional para IA local)${NC}"
fi

# 6. VERIFICAR ARCHIVOS CLAVE
echo ""
echo "6️⃣  Verificando archivos clave..."

FILES_OK=0
FILES_TOTAL=0

check_file() {
    FILES_TOTAL=$((FILES_TOTAL + 1))
    if [ -f "$1" ]; then
        echo -e "   ${GREEN}✅${NC} $1"
        FILES_OK=$((FILES_OK + 1))
    else
        echo -e "   ${RED}❌${NC} $1"
    fi
}

check_file "run.py"
check_file "services/ai_service.py"
check_file "services/document_generator.py"
check_file "services/lexnet_analyzer.py"
check_file "services/ocr_service.py"
check_file "templates/index.html"
check_file "static/js/app.js"
check_file "static/css/style.css"

echo ""
echo "   Total: $FILES_OK/$FILES_TOTAL archivos OK"

# 7. VERIFICAR DIRECTORIO EXPEDIENTES
echo ""
echo "7️⃣  Verificando directorios..."

EXPEDIENTES_DIR="$HOME/Desktop/EXPEDIENTES"
if [ ! -d "$EXPEDIENTES_DIR" ]; then
    echo -e "${YELLOW}⚠️  Creando ~/Desktop/EXPEDIENTES${NC}"
    mkdir -p "$EXPEDIENTES_DIR/_GENERADOS"
    mkdir -p "$EXPEDIENTES_DIR/2026"
else
    echo -e "${GREEN}✅ ~/Desktop/EXPEDIENTES existe${NC}"
fi

# 8. VERIFICAR .env
echo ""
echo "8️⃣  Verificando configuración API..."
if [ -f ".env" ]; then
    echo -e "${GREEN}✅ Archivo .env encontrado${NC}"
    
    # Verificar claves configuradas
    if grep -q "GROQ_API_KEY=" .env && ! grep -q "GROQ_API_KEY=$" .env; then
        echo -e "   ${GREEN}✅${NC} GROQ_API_KEY configurada"
    else
        echo -e "   ${YELLOW}⚠️${NC}  GROQ_API_KEY no configurada (opcional)"
    fi
    
    if grep -q "OPENAI_API_KEY=" .env && ! grep -q "OPENAI_API_KEY=$" .env; then
        echo -e "   ${GREEN}✅${NC} OPENAI_API_KEY configurada"
    else
        echo -e "   ${YELLOW}⚠️${NC}  OPENAI_API_KEY no configurada (opcional)"
    fi
else
    echo -e "${YELLOW}⚠️  Archivo .env no encontrado. Creando desde ejemplo...${NC}"
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Archivo .env creado${NC}"
    fi
fi

# 9. RESUMEN FINAL
echo ""
echo "=============================================="
echo "📋 RESUMEN DEL DIAGNÓSTICO"
echo "=============================================="
echo ""
echo -e "Archivos principales:    ${GREEN}$FILES_OK/$FILES_TOTAL OK${NC}"
echo -e "Entorno virtual:         ${GREEN}✅ Activado${NC}"
echo -e "Dependencias:            ${GREEN}✅ Instaladas${NC}"
echo -e "Directorio expedientes:  ${GREEN}✅ OK${NC}"
echo ""

# 10. PREGUNTAR SI ARRANCAR
echo "=============================================="
echo "🚀 ¿INICIAR EL SERVIDOR?"
echo "=============================================="
echo ""
echo "El diagnóstico está completo. Opciones:"
echo ""
echo "  1) Arrancar servidor (puerto 5002)"
echo "  2) Ver logs de última ejecución"
echo "  3) Salir"
echo ""
read -p "Selecciona opción [1-3]: " OPTION

case $OPTION in
    1)
        echo ""
        echo -e "${GREEN}🚀 Iniciando LexDocsPro LITE v2.0...${NC}"
        echo ""
        echo "=============================================="
        echo "Servidor corriendo en: http://localhost:5002"
        echo "Presiona Ctrl+C para detener"
        echo "=============================================="
        echo ""
        python run.py
        ;;
    2)
        echo ""
        echo "📜 Últimas líneas del log (si existe):"
        if [ -f "lexdocspro.log" ]; then
            tail -50 lexdocspro.log
        else
            echo "No hay archivo de log disponible"
        fi
        ;;
    3)
        echo ""
        echo "Saliendo. El entorno virtual sigue activo."
        echo "Para arrancar manualmente: python run.py"
        ;;
    *)
        echo "Opción inválida"
        ;;
esac
