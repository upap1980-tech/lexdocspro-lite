#!/bin/bash

# Test Suite - LexNET Notifications System
# LexDocsPro LITE v2.0

echo "============================================"
echo "🧪 Test Suite - LexNET Notifications"
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

# ============================================
# PRE-REQUISITOS
# ============================================
echo "📋 Verificando pre-requisitos..."

# Verificar servidor
if ! curl -s "$BASE_URL" > /dev/null; then
    echo -e "${RED}❌ Servidor NO está corriendo en $BASE_URL${NC}"
    exit 1
else
    pass_test "Servidor accesible"
fi

# Verificar PyPDF2 (necesario para parser)
if ! python3 -c "import PyPDF2" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  PyPDF2 no instalado. Instalando...${NC}"
    pip3 install PyPDF2 -q
fi

# ============================================
# AUTENTICACIÓN
# ============================================
echo ""
echo "🔐 Login..."

read -p "Email: " USER_EMAIL
read -sp "Password: " USER_PASSWORD
echo ""

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/auth/login" \
    -H "Content-Type: application/json" \
    -d "{\"email\":\"$USER_EMAIL\",\"password\":\"$USER_PASSWORD\"}")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    fail_test "Login" "No se pudo obtener token"
    exit 1
else
    pass_test "Login exitoso"
fi

# ============================================
# TEST 1: Crear PDF de prueba
# ============================================
echo ""
echo "📄 Test 1: Crear PDF de notificación LexNET de prueba"

TEST_PDF="/tmp/test_lexnet_notification.pdf"

# Crear PDF simple con texto de notificación
cat > "$TEST_PDF" << 'EOF'
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
/Length 450
>>
stream
BT
/F1 14 Tf
50 800 Td
(NOTIFICACIÓN LEXNET) Tj
0 -30 Td
/F1 10 Tf
(Procedimiento: 123/2026) Tj
0 -20 Td
(Juzgado de Primera Instancia nº 1 de Santa Cruz de La Palma) Tj
0 -20 Td
(Fecha de notificación: 01/02/2026 10:30) Tj
0 -30 Td
(SENTENCIA) Tj
0 -30 Td
(Se notifica SENTENCIA dictada en el procedimiento de referencia) Tj
0 -20 Td
(Plazo para RECURSO DE APELACIÓN: 20 días) Tj
0 -30 Td
(Demandante: MARÍA PÉREZ GARCÍA) Tj
0 -20 Td
(Demandado: JUAN LÓPEZ RODRÍGUEZ) Tj
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
867
%%EOF
EOF

if [ -f "$TEST_PDF" ]; then
    pass_test "PDF de prueba creado"
else
    fail_test "No se pudo crear PDF de prueba" "Verificar permisos"
    exit 1
fi

# ============================================
# TEST 2: Upload de notificación LexNET
# ============================================
echo ""
echo "📤 Test 2: Subir notificación LexNET"

UPLOAD_RESPONSE=$(curl -s -X POST "$BASE_URL/api/lexnet/upload-notification" \
    -H "Authorization: Bearer $TOKEN" \
    -F "file=@$TEST_PDF")

echo "Respuesta upload:"
echo "$UPLOAD_RESPONSE" | python3 -m json.tool 2>/dev/null | head -40

UPLOAD_SUCCESS=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$UPLOAD_SUCCESS" = "True" ]; then
    pass_test "Notificación LexNET subida y parseada correctamente"
    
    # Verificar campos extraídos
    NOTIF_ID=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notification_id', 0))" 2>/dev/null)
    
    if [ "$NOTIF_ID" -gt 0 ]; then
        pass_test "Notificación guardada en BD (ID: $NOTIF_ID)"
    else
        fail_test "Notificación NO guardada en BD" "ID no válido"
    fi
    
    # Verificar urgencia
    URGENCY=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notification_data', {}).get('urgency', 'NONE'))" 2>/dev/null)
    
    if [ -n "$URGENCY" ] && [ "$URGENCY" != "NONE" ]; then
        pass_test "Urgencia detectada: $URGENCY"
    else
        fail_test "Urgencia NO detectada" "Debería ser CRITICAL, URGENT, WARNING o NORMAL"
    fi
    
    # Verificar deadline
    DEADLINE=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notification_data', {}).get('deadline', ''))" 2>/dev/null)
    
    if [ -n "$DEADLINE" ]; then
        pass_test "Deadline calculado: $DEADLINE"
    else
        fail_test "Deadline NO calculado" "Verificar lógica de cálculo"
    fi
    
else
    fail_test "Upload de notificación falló" "$UPLOAD_RESPONSE"
fi

# ============================================
# TEST 3: Listar notificaciones
# ============================================
echo ""
echo "📋 Test 3: Listar notificaciones"

LIST_RESPONSE=$(curl -s "$BASE_URL/api/lexnet/notifications?unread=true" \
    -H "Authorization: Bearer $TOKEN")

LIST_SUCCESS=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$LIST_SUCCESS" = "True" ]; then
    pass_test "Endpoint /notifications responde"
    
    NOTIF_COUNT=$(echo "$LIST_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', 0))" 2>/dev/null)
    
    if [ "$NOTIF_COUNT" -gt 0 ]; then
        pass_test "Notificaciones listadas: $NOTIF_COUNT"
    else
        echo -e "${YELLOW}⚠️  ADVERTENCIA: No hay notificaciones (posible si es primera ejecución)${NC}"
    fi
else
    fail_test "Endpoint /notifications falló" "$LIST_RESPONSE"
fi

# ============================================
# TEST 4: Contador de urgentes
# ============================================
echo ""
echo "🔔 Test 4: Contador de notificaciones urgentes"

COUNT_RESPONSE=$(curl -s "$BASE_URL/api/lexnet/urgent-count" \
    -H "Authorization: Bearer $TOKEN")

COUNT_SUCCESS=$(echo "$COUNT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)

if [ "$COUNT_SUCCESS" = "True" ]; then
    pass_test "Endpoint /urgent-count responde"
    
    URGENT_COUNT=$(echo "$COUNT_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('urgent_count', -1))" 2>/dev/null)
    
    if [ "$URGENT_COUNT" -ge 0 ]; then
        pass_test "Notificaciones urgentes: $URGENT_COUNT"
        
        if [ "$URGENT_COUNT" -gt 0 ]; then
            echo "   🔴 HAY NOTIFICACIONES URGENTES - El badge debería mostrarse"
        fi
    else
        fail_test "Contador urgente inválido" "Valor: $URGENT_COUNT"
    fi
else
    fail_test "Endpoint /urgent-count falló" "$COUNT_RESPONSE"
fi

# ============================================
# TEST 5: Marcar como leída
# ============================================
echo ""
echo "✅ Test 5: Marcar notificación como leída"

if [ -n "$NOTIF_ID" ] && [ "$NOTIF_ID" -gt 0 ]; then
    READ_RESPONSE=$(curl -s -X PATCH "$BASE_URL/api/lexnet/notifications/$NOTIF_ID/read" \
        -H "Authorization: Bearer $TOKEN")
    
    READ_SUCCESS=$(echo "$READ_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('success', False))" 2>/dev/null)
    
    if [ "$READ_SUCCESS" = "True" ]; then
        pass_test "Notificación marcada como leída"
    else
        fail_test "No se pudo marcar como leída" "$READ_RESPONSE"
    fi
else
    echo -e "${YELLOW}⚠️  SKIP: No hay ID de notificación para marcar${NC}"
fi

# ============================================
# TEST 6: Verificar parsing de procedimiento
# ============================================
echo ""
echo "🔍 Test 6: Verificar extracción de datos"

PROC_NUM=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notification_data', {}).get('procedure_number', ''))" 2>/dev/null)

if echo "$PROC_NUM" | grep -q "123/2026"; then
    pass_test "Número de procedimiento extraído: $PROC_NUM"
else
    fail_test "Número de procedimiento NO extraído correctamente" "Esperado: 123/2026, Obtenido: $PROC_NUM"
fi

COURT=$(echo "$UPLOAD_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('notification_data', {}).get('court', ''))" 2>/dev/null)

if echo "$COURT" | grep -qi "juzgado"; then
    pass_test "Juzgado extraído: $COURT"
else
    fail_test "Juzgado NO extraído" "Obtenido: $COURT"
fi

# ============================================
# LIMPIEZA
# ============================================
echo ""
echo "🧹 Limpiando archivos de prueba..."
rm -f "$TEST_PDF"
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
    echo "✅ El sistema LexNET Notifications está funcionando correctamente"
    echo ""
    echo "Próximos pasos:"
    echo "1. Integrar badge en el frontend (añadir script a index.html)"
    echo "2. Subir notificaciones LexNET reales para probar"
    echo "3. Configurar email automático para alertas CRITICAL"
    exit 0
else
    echo ""
    echo -e "${YELLOW}⚠️  Algunos tests fallaron${NC}"
    echo "Revisa los errores arriba y corrige los problemas"
    exit 1
fi
