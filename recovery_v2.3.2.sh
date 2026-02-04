#!/bin/bash

# ANTES DE EJECUTAR: Detener servidor Flask
# pkill -f "flask run"

echo "🚀 Iniciando Recuperación LexDocsPro v2.3.2..."

# 1. Crear backup de seguridad previo
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p _backups_/pre_recovery_${TIMESTAMP}
cp run.py static/js/app.js templates/index.html _backups_/pre_recovery_${TIMESTAMP}/
echo "✅ Backup previo guardado en _backups_/pre_recovery_${TIMESTAMP}/"

# 2. Restaurar archivos base v2.3.1
if [ -f "run.py.backup.20260204" ]; then
    cp run.py.backup.20260204 run.py
    echo "✅ run.py restaurado"
else
    echo "❌ Error: No se encuentra run.py.backup.20260204"
fi

if [ -f "static/js/app.js.backup.20260204" ]; then
    cp static/js/app.js.backup.20260204 static/js/app.js
    echo "✅ app.js restaurado"
else
    echo "❌ Error: No se encuentra static/js/app.js.backup.20260204"
fi

# 3. Aplicar Parches Críticos (DB Crash & Auth)
# Nota: Este script asume que run.py ya fue parchado manualmente por el Agente.
# Si se requiere reaplicar, se debe usar sed o python script.
# Como el agente ya aplicó los cambios en run.py, verificamos.

if grep -q "db.get_connection()" run.py; then
    echo "✅ Parche DB detectado en run.py"
else
    echo "⚠️ Advertencia: run.py no parece tener el parche DB (db.get_connection)"
fi

if grep -q "@jwt_required_custom" run.py; then
    echo "✅ Parche Auth detectado en run.py"
else
    echo "⚠️ Advertencia: run.py no parece tener el parche Auth"
fi

# 4. Limpieza
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +
echo "✅ Caché limpio"

echo "🏁 Recuperación completada. Reiniciar servidor: bash test_system.sh"
cp "_backups_/LexDocsPro Enterprise v3.0.html" templates/index.html
