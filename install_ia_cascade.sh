#!/bin/bash

echo "=================================================="
echo "🚀 INSTALACIÓN IA CASCADE SERVICE v3.0"
echo "=================================================="

# Verificar que estamos en el directorio correcto
if [ ! -f "run.py" ]; then
    echo "❌ Error: Ejecuta este script desde el directorio raíz del proyecto"
    exit 1
fi

# Activar entorno virtual
echo ""
echo "📦 Activando entorno virtual..."
if [ -d "venv" ]; then
    source venv/bin/activate
else
    echo "❌ Error: No se encontró el entorno virtual"
    echo "   Crea uno con: python3 -m venv venv"
    exit 1
fi

# Instalar dependencias
echo ""
echo "📥 Instalando dependencias..."
pip install -q requests python-dotenv

# Verificar archivo .env
echo ""
echo "🔧 Verificando configuración..."
if [ ! -f ".env" ]; then
    echo "⚠️ Archivo .env no encontrado, creando uno nuevo..."
    cat > .env << EOF
# IA CASCADE CONFIGURATION
DEFAULT_AI_PROVIDER=ollama
OLLAMA_URL=http://localhost:11434/api/generate
OLLAMA_MODEL=llama3.2
GROQ_API_KEY=
GROQ_MODEL=llama-3.1-70b-versatile
PERPLEXITY_API_KEY=
OPENAI_API_KEY=
GEMINI_API_KEY=
DEEPSEEK_API_KEY=
CLAUDE_API_KEY=
EOF
    echo "✅ Archivo .env creado. Edítalo para añadir tus API keys."
fi

# Crear directorio de tests si no existe
if [ ! -d "tests" ]; then
    mkdir -p tests
    echo "✅ Directorio tests/ creado"
fi

# Verificar que el servicio existe
if [ ! -f "services/ia_cascade_service.py" ]; then
    echo "❌ Error: services/ia_cascade_service.py no encontrado"
    echo "   Asegúrate de haber creado el archivo del servicio"
    exit 1
fi

# Ejecutar tests
echo ""
echo "🧪 Ejecutando tests..."
python tests/test_ia_cascade.py

# Verificar resultado
if [ $? -eq 0 ]; then
    echo ""
    echo "=================================================="
    echo "✅ INSTALACIÓN COMPLETADA EXITOSAMENTE"
    echo "=================================================="
    echo ""
    echo "📋 PRÓXIMOS PASOS:"
    echo ""
    echo "1. Edita .env y añade tus API keys:"
    echo "   nano .env"
    echo ""
    echo "2. Inicia el servidor:"
    echo "   python run.py"
    echo ""
    echo "3. Abre el navegador:"
    echo "   http://127.0.0.1:5001"
    echo ""
    echo "4. Ve a la sección 'IA Cascade' en el sidebar"
    echo ""
    echo "=================================================="
else
    echo ""
    echo "❌ Algunos tests fallaron. Revisa los errores arriba."
    echo "   El sistema puede funcionar parcialmente."
fi

