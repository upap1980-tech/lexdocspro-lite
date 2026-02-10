#!/bin/bash

# Script de testing automático para LexDocsPro LITE v2.0
# Tests de OCR y Auto-Processor

echo "============================================"
echo "🧪 Testing LexDocsPro LITE v2.0"
echo "============================================"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador de tests
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# URL base
BASE_URL="http://localhost:5002"

# Función para test exitoso
test_pass() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

# Función para test fallido
test_fail() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

# Verificar que el servidor está corriendo
echo ""
echo "📡 Verificando servidor..."
if curl -s "$BASE_URL" > /dev/null; then
    test_pass "Servidor accesible en $BASE_URL"
else
    test_fail "Servidor NO accesible en $BASE_URL"
    echo "❌ Inicia el servidor con: python run.py"
    exit 1
fi

# ============================================
# TEST 1: Login y obtener token
# ============================================
echo ""
echo "🔐 Test 1: Autenticación"

# Solicitar credenciales
read -p "Email de usuario (ej: admin@lexdocs.com): " USER_EMAIL
read -sp "Contraseña: " USER_PASSWORD
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$TOKEN" ]; then
    test_pass "Login exitoso, token obtenido"
else
    test_fail "Login fallido"
    echo "Respuesta: $LOGIN_RESPONSE"
fi

# ============================================
# TEST 2: Auto-Processor Status
# ============================================
echo ""
echo "📊 Test 2: Auto-Processor Status"

STATUS_RESPONSE=$(curl -s "$BASE_URL/api/autoprocessor/status")
RUNNING=$(echo "$STATUS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('running', False))" 2>/dev/null)

if [ "$RUNNING" = "True" ] || [ "$RUNNING" = "False" ]; then
    test_pass "Endpoint /api/autoprocessor/status responde"
    echo "   Estado: Running=$RUNNING"
else
    test_fail "Endpoint /api/autoprocessor/status no responde correctamente"
fi

# ============================================
# TEST 3: Iniciar Auto-Processor
# ============================================
echo ""
echo "▶️  Test 3: Iniciar Auto-Processor"

if [ -z "$TOKEN" ]; then
    test_fail "No hay token, saltando test"
else
    START_RESPONSE=$(curl -s -X POST "$BASE_URL/api/autoprocessor/start" \
        -H "Authorization: Bearer $TOKEN")
    
    SUCCESS=$(echo "$START_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    
    if [ "$SUCCESS" = "True" ]; then
        test_pass "Auto-processor iniciado"
    elif echo "$START_RESPONSE" | grep -q "ya está corriendo"; then
        test_pass "Auto-processor ya estaba corriendo"
    else
        test_fail "Error al iniciar auto-processor"
        echo "   Respuesta: $START_RESPONSE"
    fi
fi

# ============================================
# TEST 4: Crear imagen de prueba y OCR
# ============================================
echo ""
echo "🖼️  Test 4: OCR de Imagen"

# Crear imagen de prueba con ImageMagick si está disponible
if command -v convert &> /dev/null; then
    TEST_IMG="/tmp/test_ocr_$(date +%s).png"
    convert -size 800x200 xc:white \
        -font Helvetica -pointsize 40 \
        -draw "text 50,100 'TEST OCR LexDocsPro 2026'" \
        "$TEST_IMG" 2>/dev/null
    
    if [ -f "$TEST_IMG" ]; then
        echo "   Imagen de prueba creada: $TEST_IMG"
        
        OCR_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ocr/upload" \
            -F "file=@$TEST_IMG")
        
        OCR_SUCCESS=$(echo "$OCR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
        
        if [ "$OCR_SUCCESS" = "True" ]; then
            test_pass "OCR de imagen exitoso"
            TEXT=$(echo "$OCR_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('text', '')[:100])" 2>/dev/null)
            echo "   Texto extraído: $TEXT..."
        else
            test_fail "OCR de imagen fallido"
            echo "   Respuesta: $OCR_RESPONSE"
        fi
        
        # Limpiar
        rm "$TEST_IMG"
    else
        echo -e "${YELLOW}⚠️  SKIP${NC}: No se pudo crear imagen de prueba"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP${NC}: ImageMagick no instalado (brew install imagemagick)"
fi

# ============================================
# TEST 5: Validación de archivo no soportado
# ============================================
echo ""
echo "🚫 Test 5: Validación de Formato"

# Crear archivo .txt
TEST_TXT="/tmp/test_invalid.txt"
echo "Este es un archivo de texto" > "$TEST_TXT"

INVALID_RESPONSE=$(curl -s -X POST "$BASE_URL/api/ocr/upload" \
    -F "file=@$TEST_TXT")

if echo "$INVALID_RESPONSE" | grep -q "no soportado"; then
    test_pass "Validación de formato funciona correctamente"
else
    test_fail "Validación de formato no funciona"
    echo "   Respuesta: $INVALID_RESPONSE"
fi

rm "$TEST_TXT"

# ============================================
# TEST 6: Logs del Auto-Processor
# ============================================
echo ""
echo "📝 Test 6: Logs del Auto-Processor"

if [ -z "$TOKEN" ]; then
    test_fail "No hay token, saltando test"
else
    LOGS_RESPONSE=$(curl -s "$BASE_URL/api/autoprocessor/logs?limit=5" \
        -H "Authorization: Bearer $TOKEN")
    
    if echo "$LOGS_RESPONSE" | grep -q "logs"; then
        test_pass "Endpoint de logs funciona"
        echo "   Últimos logs:"
        echo "$LOGS_RESPONSE" | python3 -c "
import sys, json
data = json.load(sys.stdin)
logs = data.get('logs', [])
for log in logs[-3:]:
    print(f\"   [{log.get('level')}] {log.get('message')}\")
" 2>/dev/null
    else
        test_fail "Endpoint de logs no responde"
    fi
fi

# ============================================
# TEST 7: Formatos soportados por OCR
# ============================================
echo ""
echo "📋 Test 7: Formatos Soportados"

# Verificar que el servicio reporta formatos correctamente
python3 << 'EOF'
import sys
sys.path.insert(0, '/Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE')

try:
    from services.ocr_service import OCRService
    ocr = OCRService()
    formats = ocr.get_supported_formats()
    
    expected = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp', '.pdf']
    
    print(f"   Formatos soportados: {', '.join(formats)}")
    
    if all(fmt in formats for fmt in expected):
        print("✅ Todos los formatos esperados están soportados")
        sys.exit(0)
    else:
        print("❌ Faltan formatos esperados")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
EOF

if [ $? -eq 0 ]; then
    test_pass "OCR soporta todos los formatos requeridos"
else
    test_fail "OCR no soporta todos los formatos"
fi

# ============================================
# RESUMEN FINAL
# ============================================
echo ""
echo "============================================"
echo "📊 RESUMEN DE TESTS"
echo "============================================"
echo "Total: $TOTAL_TESTS"
echo -e "${GREEN}Pasados: $PASSED_TESTS${NC}"
echo -e "${RED}Fallidos: $FAILED_TESTS${NC}"

if [ $FAILED_TESTS -eq 0 ]; then
    echo ""
    echo -e "${GREEN}🎉 TODOS LOS TESTS PASARON${NC}"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Algunos tests fallaron${NC}"
    exit 1
fi
