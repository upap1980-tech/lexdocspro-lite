#!/usr/bin/env bash
# fix_tab_visibility.sh

INDEX_HTML="templates/index.html"

echo "🔧 Corrigiendo visibilidad del tab Auto-Procesador..."

# Verificar que el div del tab existe
if grep -q 'id="tab-autoprocesador"' "${INDEX_HTML}"; then
    echo "✓ El div tab-autoprocesador existe"
    
    # Verificar si tiene la clase hidden por defecto
    if grep -q 'tab-autoprocesador.*hidden' "${INDEX_HTML}"; then
        echo "⚠️ PROBLEMA: El tab tiene clase 'hidden' por defecto"
        # Remover hidden del tab autoprocesador
        sed -i.bak 's/\(id="tab-autoprocesador".*\)hidden/\1/' "${INDEX_HTML}"
        echo "✓ Clase 'hidden' removida"
    fi
    
    # Verificar estructura de divs
    echo ""
    echo "📋 Estructura encontrada:"
    grep -A 2 'id="tab-autoprocesador"' "${INDEX_HTML}"
    
else
    echo "❌ ERROR: No se encuentra el div tab-autoprocesador"
    echo "El script de integración puede no haber funcionado correctamente"
fi

echo ""
echo "🔄 Reinicia el servidor Flask y recarga la página"
