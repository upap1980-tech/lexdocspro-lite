#!/usr/bin/env bash
# fix_autoprocesador_tab.sh - Corrección definitiva

PROJECT_ROOT="$(pwd)"
BACKUP_DIR="${PROJECT_ROOT}/_fix_backup_$(date +%Y%m%d_%H%M%S)"

echo "🔧 Corrigiendo visualización del tab Auto-Procesador..."
mkdir -p "${BACKUP_DIR}"

# Backup
cp templates/index.html "${BACKUP_DIR}/"
cp static/js/app.js "${BACKUP_DIR}/"

echo "✓ Backups creados en ${BACKUP_DIR}"

# ============================================
# FIX 1: Verificar que el div existe y no tiene 'hidden'
# ============================================

echo ""
echo "📋 Verificando estructura del tab..."

if grep -q '<div id="tab-autoprocesador" class="tab-content">' templates/index.html; then
    echo "✓ Tab encontrado correctamente"
else
    echo "⚠️ Corrigiendo estructura del tab..."
    # Asegurar que no tenga 'hidden' por defecto
    sed -i.tmp 's/<div id="tab-autoprocesador" class="tab-content hidden">/<div id="tab-autoprocesador" class="tab-content">/' templates/index.html
    rm -f templates/index.html.tmp
fi

# ============================================
# FIX 2: Añadir función switchTab mejorada al inicio de app.js
# ============================================

echo ""
echo "🔧 Corrigiendo función switchTab..."

# Crear función switchTab mejorada
cat > _switchtab_fix.js <<'JSFIX'
// ============================================
// SWITCH TAB - FUNCIÓN MEJORADA
// ============================================

function switchTab(tabName) {
    console.log('🔄 Cambiando a tab:', tabName);
    
    // Remover clase active de todos los tabs y botones
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Activar tab seleccionado
    const selectedTab = document.getElementById(`tab-${tabName}`);
    if (selectedTab) {
        selectedTab.classList.add('active');
        console.log('✓ Tab activado:', tabName);
    } else {
        console.error('❌ Tab no encontrado:', tabName);
    }
    
    // Activar botón correspondiente
    event.currentTarget.classList.add('active');
    
    // Si es el tab de autoprocesador, cargar datos
    if (tabName === 'autoprocesador') {
        console.log('📊 Cargando datos del auto-procesador...');
        if (typeof loadAutoProcesadorData === 'function') {
            loadAutoProcesadorData();
        } else {
            console.error('❌ Función loadAutoProcesadorData no encontrada');
        }
    }
}

JSFIX

# Verificar si switchTab ya existe en app.js
if grep -q "function switchTab" static/js/app.js; then
    echo "⚠️ switchTab ya existe, reemplazando..."
    
    # Crear archivo temporal sin la función switchTab antigua
    python3 <<PYEOF
with open('static/js/app.js', 'r', encoding='utf-8') as f:
    content = f.read()

# Buscar y eliminar función switchTab existente (incluyendo versión envuelta en IIFE)
import re

# Eliminar versión IIFE si existe
content = re.sub(r'\(function\(\) \{[^}]*window\.switchTab = function.*?\}\)\(\);', '', content, flags=re.DOTALL)

# Eliminar versión simple si existe
content = re.sub(r'function switchTab\([^)]*\) \{[^}]*\}', '', content, flags=re.DOTALL)

# Limpiar líneas vacías múltiples
content = re.sub(r'\n{3,}', '\n\n', content)

with open('static/js/app.js', 'w', encoding='utf-8') as f:
    f.write(content)

print("✓ Función switchTab antigua eliminada")
PYEOF

fi

# Insertar nueva función switchTab AL INICIO del archivo
cat _switchtab_fix.js static/js/app.js > _temp_app.js
mv _temp_app.js static/js/app.js
rm _switchtab_fix.js

echo "✓ Nueva función switchTab añadida"

# ============================================
# FIX 3: Verificar que CSS está correcto
# ============================================

echo ""
echo "🎨 Verificando CSS..."

if grep -q ".tab-content.active" static/css/style.css; then
    echo "✓ CSS para tabs activos existe"
else
    echo "⚠️ Añadiendo CSS para tabs activos..."
    cat >> static/css/style.css <<'CSSFIX'

/* Tab visibility fix */
.tab-content {
    display: none;
}

.tab-content.active {
    display: block !important;
}
CSSFIX
fi

# ============================================
# VERIFICACIÓN FINAL
# ============================================

echo ""
echo "🔍 Verificación final..."

errors=0

if grep -q "function switchTab" static/js/app.js; then
    echo "✓ switchTab presente en app.js"
else
    echo "✗ switchTab NO encontrado en app.js"
    ((errors++))
fi

if grep -q 'id="tab-autoprocesador"' templates/index.html; then
    echo "✓ Tab autoprocesador presente en HTML"
else
    echo "✗ Tab autoprocesador NO encontrado en HTML"
    ((errors++))
fi

if grep -q "loadAutoProcesadorData" static/js/app.js; then
    echo "✓ Funciones autoprocesador presentes en JS"
else
    echo "✗ Funciones autoprocesador NO encontradas en JS"
    ((errors++))
fi

echo ""
if [[ ${errors} -eq 0 ]]; then
    echo "✅ CORRECCIÓN COMPLETADA CON ÉXITO"
    echo ""
    echo "📋 Pasos siguientes:"
    echo "  1. Reinicia el servidor Flask (Ctrl+C, luego python run.py)"
    echo "  2. Recarga el navegador con Cmd+Shift+R"
    echo "  3. Haz clic en 🤖 Auto-Procesador"
    echo "  4. Abre la consola (F12) para ver logs de depuración"
else
    echo "⚠️ Se encontraron ${errors} problemas"
    echo "Revisa los mensajes arriba"
fi
