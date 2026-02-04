#!/bin/bash

BASE_URL="http://localhost:5001"
echo "🧪 Probando endpoints del Auto-Procesador en ${BASE_URL}"
echo "================================================"

echo ""
echo "1️⃣ Estadísticas generales:"
curl -s "${BASE_URL}/api/autoprocesador/stats" | python3 -m json.tool

echo ""
echo "2️⃣ Cola de revisión:"
curl -s "${BASE_URL}/api/autoprocesador/cola-revision" | python3 -m json.tool

echo ""
echo "3️⃣ Procesados hoy:"
curl -s "${BASE_URL}/api/autoprocesador/procesados-hoy" | python3 -m json.tool

echo ""
echo "4️⃣ Lista de clientes:"
curl -s "${BASE_URL}/api/autoprocesador/clientes" | python3 -m json.tool

echo ""
echo "✅ Pruebas completadas"
