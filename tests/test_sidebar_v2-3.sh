#!/bin/bash
# tests/test_sidebar_v2-3.sh
# Verificación de integridad para la Sidebar v2.3.1 Sidebar Classic

echo "============================================"
echo "🧪 SIDEBAR VERIFICATION - LexDocsPro LITE v2.3.1"
echo "============================================"

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

CHECK_FILE="templates/index.html"

# 1. Verificar existencia de la Sidebar
echo "🔍 Verificando estructura de la Sidebar..."
if grep -q "class=\"sidebar-v2-3\"" "$CHECK_FILE"; then
    echo -e "${GREEN}✅ Sidebar v2.3.1 encontrada${NC}"
else
    echo -e "${RED}❌ Sidebar no encontrada en index.html${NC}"
    exit 1
fi

# 2. Verificar los 15 items
echo "🔍 Verificando los 15 items de navegación..."
ITEMS=(
    "dashboard" "processor" "cascade" "preview" "email"
    "signature" "banking" "users" "pwa" "agent"
    "analytics" "expedientes" "lexnet" "settings" "deploy"
)

for item in "${ITEMS[@]}"; do
    if grep -q "data-panel=\"$item\"" "$CHECK_FILE"; then
        echo -e "${GREEN}✅ Item [$item] verificado${NC}"
    else
        echo -e "${RED}❌ Item [$item] falta en la navegación${NC}"
        exit 1
    fi
done

# 3. Verificar los 15 paneles
echo "🔍 Verificando los 15 paneles de contenido..."
for item in "${ITEMS[@]}"; do
    if grep -q "id=\"panel-$item\"" "$CHECK_FILE"; then
        echo -e "${GREEN}✅ Panel [panel-$item] verificado${NC}"
    else
        echo -e "${RED}❌ Panel [panel-$item] falta en el DOM${NC}"
        exit 1
    fi
done

# 4. Verificar limpieza fiscal
echo "🔍 Verificando ausencia de rastro fiscal (347)..."
if grep -i "347" "$CHECK_FILE" | grep -v "sidebar-v2-3"; then
    echo -e "${RED}❌ Se detectaron referencias al Modelo 347 en index.html${NC}"
    exit 1
else
    echo -e "${GREEN}✅ Sistema limpio de referencias fiscales${NC}"
fi

echo "============================================"
echo "🎉 VERIFICACIÓN COMPLETADA: 100% SUCCESS"
echo "============================================"
