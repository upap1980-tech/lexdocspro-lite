#!/bin/bash

# Master Test Suite - LexDocsPro LITE v2.0.1
# Ejecuta todos los tests del sistema

echo "============================================"
echo "🧪 MASTER TEST SUITE - LexDocsPro LITE v2.0.1"
echo "============================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Contadores globales
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0

# Base URL
BASE_URL="http://localhost:5001"

# Función para ejecutar suite
run_suite() {
    local suite_name=$1
    local suite_path=$2
    
    echo ""
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${BLUE}📦 Suite: $suite_name${NC}"
    echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    
    ((TOTAL_SUITES++))
    
    if [ -f "$suite_path" ]; then
        if bash "$suite_path"; then
            echo -e "${GREEN}✅ Suite PASSED: $suite_name${NC}"
            ((PASSED_SUITES++))
            return 0
        else
            echo -e "${RED}❌ Suite FAILED: $suite_name${NC}"
            ((FAILED_SUITES++))
            return 1
        fi
    else
        echo -e "${YELLOW}⚠️  Suite no encontrada: $suite_path${NC}"
        ((FAILED_SUITES++))
        return 1
    fi
}

# Verificar servidor
echo "📋 Verificando pre-requisitos..."
if ! curl -s "$BASE_URL" > /dev/null; then
    echo -e "${RED}❌ Servidor NO está corriendo en $BASE_URL${NC}"
    echo "Por favor inicia el servidor con: python run.py"
    exit 1
else
    echo -e "${GREEN}✅ Servidor accesible${NC}"
fi

# Verificar dependencias
echo "📦 Verificando dependencias..."

DEPS_OK=true

if ! python3 -c "import PyPDF2" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  PyPDF2 no instalado${NC}"
    DEPS_OK=false
fi

if ! python3 -c "import pdf2image" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  pdf2image no instalado${NC}"
    DEPS_OK=false
fi

if ! which pdftoppm > /dev/null; then
    echo -e "${YELLOW}⚠️  poppler no instalado (necesario para pdf2image)${NC}"
    echo "   Instalar con: brew install poppler"
    DEPS_OK=false
fi

if [ "$DEPS_OK" = false ]; then
    echo -e "${YELLOW}⚠️  Algunas dependencias faltan. ¿Continuar? (y/n)${NC}"
    read -r response
    if [ "$response" != "y" ]; then
        exit 1
    fi
else
    echo -e "${GREEN}✅ Dependencias OK${NC}"
fi

# ============================================
# EJECUTAR SUITES DE TESTS
# ============================================

START_TIME=$(date +%s)

# Suite 1: Document Confirmation
run_suite "Document Confirmation" "tests/test_document_confirmation.sh"

# Suite 2: LexNET Notifications
run_suite "LexNET Notifications" "tests/test_lexnet_notifications.sh"

# Suite 3: OCR & Auto-Processor (si existe)
if [ -f "tests/test_ocr_autoprocessor.sh" ]; then
    run_suite "OCR & Auto-Processor" "tests/test_ocr_autoprocessor.sh"
fi

# ============================================
# TESTS ADICIONALES RÁPIDOS
# ============================================

echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${BLUE}🔬 Tests Adicionales${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""

# Test: Health check
echo "🏥 Test: Health check..."
HEALTH=$(curl -s "$BASE_URL/api/health" 2>/dev/null)
if echo "$HEALTH" | grep -q "ok"; then
    echo -e "${GREEN}✅ Health check OK${NC}"
else
    echo -e "${YELLOW}⚠️  Health check endpoint no disponible${NC}"
fi

# Test: Stats endpoint
echo "📊 Test: Dashboard stats..."
# Necesita autenticación, así que solo verificamos que el endpoint existe
STATS_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/dashboard/stats" -H "Authorization: Bearer invalid_token")
if [ "$STATS_CODE" = "401" ] || [ "$STATS_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Stats endpoint exists${NC}"
else
    echo -e "${RED}❌ Stats endpoint error (code: $STATS_CODE)${NC}"
fi

# Test: PDF Preview endpoint
echo "🖼️  Test: PDF Preview endpoint..."
PREVIEW_CODE=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/api/document/preview" -X POST -H "Authorization: Bearer invalid_token")
if [ "$PREVIEW_CODE" = "401" ] || [ "$PREVIEW_CODE" = "400" ]; then
    echo -e "${GREEN}✅ Preview endpoint exists${NC}"
else
    echo -e "${RED}❌ Preview endpoint error (code: $PREVIEW_CODE)${NC}"
fi

# ============================================
# RESUMEN FINAL
# ============================================

END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))

echo ""
echo "============================================"
echo "📊 RESUMEN FINAL"
echo "============================================"
echo ""
echo "Suites ejecutadas: $TOTAL_SUITES"
echo -e "${GREEN}Suites pasadas: $PASSED_SUITES${NC}"
echo -e "${RED}Suites falladas: $FAILED_SUITES${NC}"
echo ""
echo "Tiempo total: ${ELAPSED}s"
echo ""

# Calcular porcentaje
if [ $TOTAL_SUITES -gt 0 ]; then
    SUCCESS_RATE=$((PASSED_SUITES * 100 / TOTAL_SUITES))
    echo "Tasa de éxito: ${SUCCESS_RATE}%"
fi

echo ""

if [ $FAILED_SUITES -eq 0 ]; then
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${GREEN}🎉 TODAS LAS SUITES PASARON${NC}"
    echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "✅ El sistema está listo para producción"
    echo ""
    echo "📋 Pending Tasks:"
    echo "1. Integrar HTML/CSS/JS en templates/index.html"
    echo "2. Actualizar README.md con nuevas features"
    echo "3. Crear API_REFERENCE.md"
    echo "4. Deploy a producción"
    echo ""
    exit 0
else
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo -e "${YELLOW}⚠️  ALGUNAS SUITES FALLARON${NC}"
    echo -e "${YELLOW}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
    echo ""
    echo "Revisa los errores arriba y corrige los problemas antes de deploy."
    echo ""
    exit 1
fi
