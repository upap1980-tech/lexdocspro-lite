#!/bin/bash
# Test Suite: Dashboard PDF Export (v2.2.0)

echo "============================================"
echo "🖨️  TEST SUITE - Dashboard PDF Export"
echo "============================================"

# 1. Login para obtener token
echo "🔐 1. Login..."
LOGIN_RES=$(curl -s -X POST http://localhost:5011/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@lexdocspro.com", "password":"admin123"}')

TOKEN=$(echo $LOGIN_RES | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)

if [ -z "$TOKEN" ]; then
    echo "❌ Error: No se pudo obtener token"
    exit 1
fi
echo "✅ Token obtenido"

# 2. Test Endpoint Export PDF
echo "📄 2. Test Export PDF..."
curl -s -o /tmp/dashboard_test.pdf -X GET http://localhost:5011/api/dashboard/export-pdf \
  -H "Authorization: Bearer $TOKEN"

if [ -f "/tmp/dashboard_test.pdf" ]; then
    SIZE=$(stat -f%z /tmp/dashboard_test.pdf 2>/dev/null || stat -c%s /tmp/dashboard_test.pdf)
    if [ "$SIZE" -gt 1000 ]; then
        echo "✅ PDF generado correctamente ($SIZE bytes)"
        file /tmp/dashboard_test.pdf
    else
        echo "❌ PDF demasiado pequeño o vacío ($SIZE bytes)"
        exit 1
    fi
else
    echo "❌ No se generó el archivo PDF"
    exit 1
fi

echo "============================================"
echo "🎉 Todos los tests de Export PDF pasaron"
echo "============================================"
