#!/bin/bash

# Test Suite para Document Confirmation Workflow
# LexDocsPro LITE v2.0

echo "============================================"
echo "🧪 Test Suite - Document Confirmation"
echo "============================================"
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Contador
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# Base URL
BASE_URL="http://localhost:5001"

# Función para logs
pass_test() {
    echo -e "${GREEN}✅ PASS${NC}: $1"
    ((PASSED_TESTS++))
    ((TOTAL_TESTS++))
}

fail_test() {
    echo -e "${RED}❌ FAIL${NC}: $1"
    echo -e "   ${YELLOW}Detalle: $2${NC}"
    ((FAILED_TESTS++))
    ((TOTAL_TESTS++))
}

skip_test() {
    echo -e "${YELLOW}⚠️  SKIP${NC}: $1"
}

# ============================================
# PRE-REQUISITOS
# ============================================
echo "📋 Verificando pre-requisitos..."

# Verificar que el servidor está corriendo
if ! curl -s "$BASE_URL" > /dev/null; then
    echo -e "${RED}❌ Servidor NO está corriendo en $BASE_URL${NC}"
    echo "Inicia el servidor con: python run.py"
    exit 1
else
    pass_test "Servidor accesible"
fi

# ============================================
# AUTENTICACIÓN
# ============================================
echo ""
echo "🔐 Login para obtener token JWT..."

read -p "Email: " USER_EMAIL
read -sp "Password: " USER_PASSWORD
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    fail_test "Login" "No se pudo obtener token"
    echo "Respuesta: $LOGIN_RESPONSE"
    exit 1
else
    pass_test "Login exitoso"
fi

# ============================================
# TEST 1: Obtener tipos de documentos
# ============================================
echo ""
echo "📝 Test 1: Obtener tipos de documentos"

TYPES_RESPONSE=$(curl -s "$BASE_URL/api/document/types")
TYPES_COUNT=$(echo "$TYPES_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('types', [])))" 2>/dev/null)

if [ "$TYPES_COUNT" -gt 10 ]; then
    pass_test "Tipos de documentos ($TYPES_COUNT tipos disponibles)"
    
    # Verificar tipos específicos
    if echo "$TYPES_RESPONSE" | grep -q "Escrito de Acusación"; then
        pass_test "Tipo 'Escrito de Acusación (MF)' disponible"
    else
        fail_test "Tipo 'Escrito de Acusación (MF)' NO encontrado" "Revisar document_processing_service.py"
    fi
else
    fail_test "Tipos de documentos insuficientes" "Solo $TYPES_COUNT tipos"
fi

# ============================================
# TEST 2: Crear archivo temporal de prueba
# ============================================
echo ""
echo "📄 Test 2: Crear archivo temporal de prueba"

TEST_FILE="/tmp/test_document_$(date +%s).pdf"

# Crear PDF simple de prueba con texto
cat > "$TEST_FILE" << 'EOF'
%PDF-1.4
1 0 obj
<<
/Type /Catalog
/Pages 2 0 R
>>
endobj
2 0 obj
<<
/Type /Pages
/Kids [3 0 R]
/Count 1
>>
endobj
3 0 obj
<<
/Type /Page
/Parent 2 0 R
/MediaBox [0 0 595 842]
/Contents 4 0 R
/Resources <<
/Font <<
/F1 <<
/Type /Font
/Subtype /Type1
/BaseFont /Times-Roman
>>
>>
>>
>>
endobj
4 0 obj
<<
/Length 200
>>
stream
BT
/F1 12 Tf
50 800 Td
(Cliente: María Pérez García) Tj
0 -20 Td
(Tipo: Escrito de Acusación del Ministerio Fiscal) Tj
0 -20 Td
(Fecha: 15/03/2022) Tj
0 -20 Td
(Expediente: 123/2022) Tj
0 -20 Td
(Juzgado: Juzgado de Instrucción nº 3 Madrid) Tj
ET
endstream
endobj
xref
0 5
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000366 00000 n
trailer
<<
/Size 5
/Root 1 0 R
>>
startxref
617
%%EOF
EOF

if [ -f "$TEST_FILE" ]; then
    pass_test "Archivo temporal creado: $TEST_FILE"
else
    fail_test "No se pudo crear archivo temporal" "Verificar permisos /tmp/"
    exit 1
fi

# ============================================
# TEST 3: Proponer guardado (propose-save)
# ============================================
echo ""
echo "🤖 Test 3: Proponer guardado con IA"

PROPOSE_RESPONSE=$(curl -s -X POST "$BASE_URL/api/document/propose-save" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"temp_file_path\": \"$TEST_FILE\",
        \"hint_year\": 2026
    }")

echo "Respuesta propose-save:"
echo "$PROPOSE_RESPONSE" | python3 -m json.tool 2>/dev/null | head -30

PROPOSE_SUCCESS=$(echo "$PROPOSE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$PROPOSE_SUCCESS" = "True" ]; then
    pass_test "Endpoint /propose-save responde correctamente"
    
    # Verificar campos del proposal
    SUGGESTED_PATH=$(echo "$PROPOSE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('proposal', {}).get('suggested_path', ''))" 2>/dev/null)
    
    if [ -n "$SUGGESTED_PATH" ]; then
        pass_test "Ruta sugerida generada: $SUGGESTED_PATH"
        
        # Verificar que contiene el año correcto (2026, no 2022)
        if echo "$SUGGESTED_PATH" | grep -q "2026"; then
            pass_test "Año detectado correctamente (2026)"
        elif echo "$SUGGESTED_PATH" | grep -q "2022"; then
            fail_test "Año detectado incorrectamente (2022 en lugar de 2026)" "Revisar lógica de detección de año en document_processing_service.py"
        fi
    else
        fail_test "No se generó ruta sugerida" "Verificar propose_save()"
    fi
    
    # Extraer cliente
    CLIENT_NAME=$(echo "$PROPOSE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('proposal', {}).get('client', ''))" 2>/dev/null)
    
    if [ -n "$CLIENT_NAME" ]; then
        pass_test "Cliente extraído: $CLIENT_NAME"
    else
        fail_test "No se extrajo cliente" "Revisar extracción IA"
    fi
    
else
    fail_test "Endpoint /propose-save falló" "$PROPOSE_RESPONSE"
fi

# ============================================
# TEST 4: Path options
# ============================================
echo ""
echo "📁 Test 4: Obtener opciones de carpetas"

PATH_OPTS_RESPONSE=$(curl -s "$BASE_URL/api/document/path-options?year=2026" \
    -H "Authorization: Bearer $TOKEN")

PATH_OPTS_SUCCESS=$(echo "$PATH_OPTS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$PATH_OPTS_SUCCESS" = "True" ]; then
    pass_test "Endpoint /path-options responde"
    
    FOLDERS_COUNT=$(echo "$PATH_OPTS_RESPONSE" | python3 -c "import sys, json; print(len(json.load(sys.stdin).get('folders', [])))" 2>/dev/null)
    echo "   Carpetas encontradas para 2026: $FOLDERS_COUNT"
else
    fail_test "Endpoint /path-options falló" "$PATH_OPTS_RESPONSE"
fi

# ============================================
# TEST 5: Confirmar guardado (confirm-save)
# ============================================
echo ""
echo "💾 Test 5: Confirmar guardado de documento"

# Construir ruta de prueba
TEST_DEST_PATH="$HOME/Desktop/EXPEDIENTES/2026/2026-TEST_$(date +%s)"
mkdir -p "$TEST_DEST_PATH"

CONFIRM_RESPONSE=$(curl -s -X POST "$BASE_URL/api/document/confirm-save" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"temp_file_path\": \"$TEST_FILE\",
        \"confirmed_data\": {
            \"client\": \"María Pérez García TEST\",
            \"doc_type\": \"Escrito de Acusación (MF)\",
            \"date\": \"2022-03-15\",
            \"expedient\": \"123/2022\",
            \"court\": \"Juzgado Instrucción nº 3 Madrid\",
            \"year\": 2026,
            \"path\": \"$TEST_DEST_PATH\",
            \"filename\": \"2022-03-15_test_acusacion.pdf\"
        }
    }")

CONFIRM_SUCCESS=$(echo "$CONFIRM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$CONFIRM_SUCCESS" = "True" ]; then
    pass_test "Endpoint /confirm-save guardó documento"
    
    FINAL_PATH=$(echo "$CONFIRM_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('final_path', ''))" 2>/dev/null)
    
    if [ -f "$FINAL_PATH" ]; then
        pass_test "Archivo guardado correctamente en: $FINAL_PATH"
        
        # Limpiar
        rm -f "$FINAL_PATH"
        rmdir "$TEST_DEST_PATH" 2>/dev/null
    else
        fail_test "Archivo NO encontrado en ruta final" "$FINAL_PATH"
    fi
else
    fail_test "Endpoint /confirm-save falló" "$CONFIRM_RESPONSE"
fi

# ============================================
# TEST 6: Dashboard stats
# ============================================
echo ""
echo "📊 Test 6: Dashboard stats en tiempo real"

STATS_RESPONSE=$(curl -s "$BASE_URL/api/dashboard/stats" \
    -H "Authorization: Bearer $TOKEN")

STATS_SUCCESS=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$STATS_SUCCESS" = "True" ]; then
    pass_test "Endpoint /dashboard/stats responde"
    
    LAST_UPLOADED=$(echo "$STATS_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('last_uploaded', 0))" 2>/dev/null)
    echo "   Documentos subidos hoy: $LAST_UPLOADED"
    
    if [ "$LAST_UPLOADED" -ge 0 ]; then
        pass_test "Estadística 'last_uploaded' funcionando"
    fi
else
    fail_test "Endpoint /dashboard/stats falló" "$STATS_RESPONSE"
fi

# ============================================
# TEST 7: Validación año correcto
# ============================================
echo ""
echo "📅 Test 7: Validación detección de año correcto"

# Este test verifica que documentos de 2022 se clasifiquen en 2026 si el asunto es actual
YEAR_TEST_RESPONSE=$(curl -s -X POST "$BASE_URL/api/document/propose-save" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"temp_file_path\": \"$TEST_FILE\",
        \"extracted_data\": {
            \"client\": \"Test Cliente\",
            \"doc_type\": \"Escrito\",
            \"date\": \"15/03/2022\",
            \"confidence\": 90
        },
        \"hint_year\": 2026
    }")

DETECTED_YEAR=$(echo "$YEAR_TEST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('proposal', {}).get('suggested_year', 0))" 2>/dev/null)

if [ "$DETECTED_YEAR" = "2026" ]; then
    pass_test "Año detectado correctamente como 2026 (asunto actual, no fecha interna)"
else
    fail_test "Año detectado incorrectamente: $DETECTED_YEAR" "Debería ser 2026 por hint_year"
fi

# ============================================
# LIMPIEZA
# ============================================
echo ""
echo "🧹 Limpiando archivos de prueba..."
rm -f "$TEST_FILE"
echo "   Archivos temporales eliminados"

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
    echo ""
    echo "✅ El sistema de confirmación de documentos está funcionando correctamente"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Algunos tests fallaron${NC}"
    echo "Revisa los errores arriba y corrige los problemas"
    exit 1
fi
