#!/bin/bash
# Test de Preview Multi-Página (v2.2.0)

echo "============================================"
echo "🖼️  TEST SUITE - PDF Multi-Page Preview"
echo "============================================"

# Port
PORT=5001
BASE_URL="http://localhost:$PORT"

# Obtener token (asumiendo que admin:admin123 existe)
echo "🔐 Login..."
TOKEN=$(curl -s -X POST "$BASE_URL/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@lexdocs.com", "password": "admin123"}' | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Error: No se pudo obtener token"
    exit 1
fi

# 1. Crear un PDF multi-página ficticio para test (si no existe)
TEST_PDF="/tmp/test_multipage.pdf"
echo "📄 Creando PDF de prueba..."
python3 -c "
from fpdf import FPDF
pdf = FPDF()
for i in range(1, 6):
    pdf.add_page()
    pdf.set_font('Arial', 'B', 16)
    pdf.cell(40, 10, f'Página {i} de Contenido LexDocs')
pdf.output('$TEST_PDF')
"

# 2. Test: Endpoint de Thumbnails
echo "📊 Test: /api/document/thumbnails..."
THUMBS=$(curl -s -X POST "$BASE_URL/api/document/thumbnails" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"temp_file_path\": \"$TEST_PDF\"}")

SUCCESS=$(echo $THUMBS | grep -o '"success":true')
TOTAL=$(echo $THUMBS | grep -o '"total_pages":5')

if [ ! -z "$SUCCESS" ] && [ ! -z "$TOTAL" ]; then
    echo "✅ PASS: Thumbnails generados correctamente (5 páginas)"
else
    echo "❌ FAIL: Error en thumbnails"
    echo "Respuesta: $THUMBS"
    exit 1
fi

# 3. Test: Preview de página 3
echo "🖼️  Test: /api/document/preview (Página 3)..."
PREVIEW=$(curl -s -X POST "$BASE_URL/api/document/preview" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"temp_file_path\": \"$TEST_PDF\", \"page\": 3}")

SUCCESS_PREV=$(echo $PREVIEW | grep -o '"success":true')
IMG_DATA=$(echo $PREVIEW | grep -o '"image":"data:image/png;base64')

if [ ! -z "$SUCCESS_PREV" ] && [ ! -z "$IMG_DATA" ]; then
    echo "✅ PASS: Preview de página específica OK"
else
    echo "❌ FAIL: Error en preview de página"
    exit 1
fi

echo "============================================"
echo "🎉 TODOS LOS TESTS DE PREVIEW PASARON"
echo "============================================"
