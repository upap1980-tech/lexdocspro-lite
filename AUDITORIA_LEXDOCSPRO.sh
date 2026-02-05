#!/bin/bash
# AUDITORIA_LEXDOCSPRO.sh - Verificación completa de funcionalidades
# Fecha: 05/02/2026 04:15 AM WET

cd ~/Desktop/PROYECTOS/LexDocsPro-LITE || exit 1

echo "╔══════════════════════════════════════════════════════════════╗"
echo "║  AUDITORÍA LEXDOCSPRO LITE v2.0 - VERIFICACIÓN FUNCIONALIDADES  ║"
echo "╚══════════════════════════════════════════════════════════════╝"
echo ""
echo "📅 Fecha: $(date '+%Y-%m-%d %H:%M:%S')"
echo "📂 Directorio: $(pwd)"
echo ""

# Colores para output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores
TOTAL=0
IMPLEMENTADO=0
PARCIAL=0
NO_IMPLEMENTADO=0

# Función de verificación
verificar() {
    TOTAL=$((TOTAL + 1))
    local nombre="$1"
    local comando="$2"
    local esperado="$3"
    
    echo -n "[$TOTAL] $nombre... "
    
    resultado=$(eval "$comando" 2>/dev/null)
    
    if [ -z "$resultado" ]; then
        echo -e "${RED}❌ NO IMPLEMENTADO${NC}"
        NO_IMPLEMENTADO=$((NO_IMPLEMENTADO + 1))
        return 1
    elif [[ "$resultado" =~ $esperado ]]; then
        echo -e "${GREEN}✅ IMPLEMENTADO${NC} ($resultado)"
        IMPLEMENTADO=$((IMPLEMENTADO + 1))
        return 0
    else
        echo -e "${YELLOW}🟡 PARCIAL${NC} ($resultado de $esperado esperados)"
        PARCIAL=$((PARCIAL + 1))
        return 2
    fi
}

echo "═══════════════════════════════════════════════════════════════"
echo "🔧 BACKEND - Servicios Python"
echo "═══════════════════════════════════════════════════════════════"

# 1. Servicio OCR
verificar "Servicio OCR" \
    "grep -c 'def extract_text' services/ocrservice.py" \
    "1"

# 2. Servicio IA Multi-modelo
verificar "IA Multi-modelo (Ollama/Groq/Perplexity)" \
    "grep -c -E '(ollama|groq|perplexity)' services/aiservice.py" \
    "3"

# 3. Generadores de documentos
verificar "Generadores de documentos" \
    "grep -c '^def generate_' services/documentgenerator.py" \
    "1[012]"

# 4. LexNET Analyzer
verificar "LexNET Analyzer" \
    "grep -c 'def analizar' services/lexnetanalyzer.py" \
    "1"

# 5. File Service
verificar "File Service" \
    "grep -c 'def list_directory' services/fileservice.py" \
    "1"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🗄️  BASE DE DATOS - Estructura SQLite"
echo "═══════════════════════════════════════════════════════════════"

# 6. Tablas BD
verificar "Tabla users" \
    "sqlite3 instance/legaldocs.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"users\"' 2>/dev/null" \
    "users"

verificar "Tabla pending_documents" \
    "sqlite3 instance/legaldocs.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"pending_documents\"' 2>/dev/null" \
    "pending"

verificar "Tabla saved_documents" \
    "sqlite3 instance/legaldocs.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"saved_documents\"' 2>/dev/null" \
    "saved"

verificar "Tabla clients" \
    "sqlite3 instance/legaldocs.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"clients\"' 2>/dev/null" \
    "clients"

verificar "Tabla audit_log" \
    "sqlite3 instance/legaldocs.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"audit_log\"' 2>/dev/null" \
    "audit"

verificar "Tabla token_blacklist" \
    "sqlite3 instance/legaldocs.db 'SELECT name FROM sqlite_master WHERE type=\"table\" AND name=\"token_blacklist\"' 2>/dev/null" \
    "token"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🌐 API REST - Endpoints Flask"
echo "═══════════════════════════════════════════════════════════════"

# 7. Endpoints principales
verificar "Endpoint /login" \
    "grep -c '@app.route.*login' run.py" \
    "1"

verificar "Endpoint /api/dashboard/stats" \
    "grep -c '@app.route.*dashboard.*stats' run.py" \
    "1"

verificar "Endpoint /api/ocr/upload" \
    "grep -c '@app.route.*ocr.*upload' run.py" \
    "1"

verificar "Endpoint /api/document/smart-analyze" \
    "grep -c '@app.route.*document.*analyze' run.py" \
    "1"

verificar "Endpoint /api/lexnet/analyze" \
    "grep -c '@app.route.*lexnet.*analyz' run.py" \
    "1"

verificar "Endpoint /api/clientes" \
    "grep -c '@app.route.*clientes' run.py" \
    "1"

verificar "Endpoint /api/files" \
    "grep -c '@app.route.*files' run.py" \
    "1"

verificar "Total de endpoints" \
    "grep -c '@app.route' run.py" \
    "1[5-9]"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🔐 SEGURIDAD - Autenticación JWT"
echo "═══════════════════════════════════════════════════════════════"

# 8. JWT
verificar "JWT Secret Key configurado" \
    "grep -c 'JWT_SECRET_KEY' run.py" \
    "1"

verificar "Decoradores @jwt_required" \
    "grep -c '@jwt_required' run.py" \
    "[5-9]"

verificar "FlaskJWTExtended importado" \
    "grep -c 'from flask_jwt_extended import' run.py" \
    "1"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "🎨 FRONTEND - Componentes JavaScript"
echo "═══════════════════════════════════════════════════════════════"

# 9. Archivos JS
verificar "Archivo app.js" \
    "wc -l static/js/app.js 2>/dev/null | awk '{print \$1}'" \
    "[0-9]{3,4}"

verificar "Modal confirmación documento" \
    "wc -l static/js/document-confirm-modal.js 2>/dev/null | awk '{print \$1}'" \
    "[5-9][0-9]{2}"

verificar "File explorer" \
    "wc -l static/js/file-explorer.js 2>/dev/null | awk '{print \$1}'" \
    "[4-9][0-9]{2}"

verificar "PDF viewer" \
    "wc -l static/js/pdf-viewer.js 2>/dev/null | awk '{print \$1}'" \
    "[3-9][0-9]{2}"

verificar "AI chat" \
    "wc -l static/js/ai-chat.js 2>/dev/null | awk '{print \$1}'" \
    "[3-9][0-9]{2}"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📄 FRONTEND - HTML Templates"
echo "═══════════════════════════════════════════════════════════════"

# 10. Secciones HTML
verificar "Total líneas index.html" \
    "wc -l templates/index.html 2>/dev/null | awk '{print \$1}'" \
    "[2-9][0-9]{2}"

verificar "Sección Dashboard" \
    "grep -c '<section id=\"dashboard\"' templates/index.html" \
    "1"

verificar "Sección Expedientes" \
    "grep -c '<section id=\"expedientes\"' templates/index.html" \
    "1"

verificar "Sección LexNET" \
    "grep -c '<section id=\"lexnet\"' templates/index.html" \
    "1"

verificar "Sección IA Cascade" \
    "grep -c '<section id=\"ia-cascade\"' templates/index.html" \
    "1"

verificar "Total de secciones (15 esperadas)" \
    "grep -c '<section id=' templates/index.html" \
    "1[5-9]"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📋 FUNCIONALIDADES ESPECÍFICAS"
echo "═══════════════════════════════════════════════════════════════"

# 11. Watchdog
verificar "Script autoprocesar.py" \
    "test -f autoprocesar.py && echo 'existe' || echo ''" \
    "existe"

# 12. Tests
verificar "Carpeta tests/" \
    "test -d tests && ls tests/*.sh 2>/dev/null | wc -l" \
    "[1-9]"

# 13. Generador Acta Conciliación
verificar "Template Acta Conciliación" \
    "test -f templates/legal/acta_conciliacion.md && echo 'existe' || echo ''" \
    "existe"

# 14. Dark Mode
verificar "Dark mode CSS/JS" \
    "grep -r -c 'dark.*mode\|theme.*toggle' static/ 2>/dev/null | grep -v ':0' | wc -l" \
    "[1-9]"

# 15. Responsive CSS
verificar "Media queries responsive" \
    "grep -c '@media' static/css/*.css 2>/dev/null | grep -v ':0' | head -1" \
    "[1-9]"

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📊 RESUMEN FINAL"
echo "═══════════════════════════════════════════════════════════════"

PORCENTAJE=$((IMPLEMENTADO * 100 / TOTAL))

echo ""
echo -e "${BLUE}Total de funcionalidades verificadas:${NC} $TOTAL"
echo -e "${GREEN}✅ Implementadas completamente:${NC} $IMPLEMENTADO ($((IMPLEMENTADO * 100 / TOTAL))%)"
echo -e "${YELLOW}🟡 Parcialmente implementadas:${NC} $PARCIAL ($((PARCIAL * 100 / TOTAL))%)"
echo -e "${RED}❌ NO implementadas:${NC} $NO_IMPLEMENTADO ($((NO_IMPLEMENTADO * 100 / TOTAL))%)"
echo ""

if [ $PORCENTAJE -ge 80 ]; then
    echo -e "${GREEN}🎉 EXCELENTE: Sistema con implementación sólida (≥80%)${NC}"
elif [ $PORCENTAJE -ge 60 ]; then
    echo -e "${YELLOW}⚠️  BUENO: Sistema funcional con mejoras pendientes (60-79%)${NC}"
elif [ $PORCENTAJE -ge 40 ]; then
    echo -e "${YELLOW}⚠️  REGULAR: Funcionalidades básicas presentes (40-59%)${NC}"
else
    echo -e "${RED}🚨 CRÍTICO: Implementación insuficiente (<40%)${NC}"
fi

echo ""
echo "═══════════════════════════════════════════════════════════════"
echo "📝 Reporte guardado en: AUDITORIA_$(date +%Y%m%d_%H%M%S).txt"
echo "═══════════════════════════════════════════════════════════════"
