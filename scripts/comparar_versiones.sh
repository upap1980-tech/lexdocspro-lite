#!/bin/bash

echo "=============================================="
echo "🔍 COMPARACIÓN DE VERSIONES LexDocsPro LITE"
echo "=============================================="
echo ""

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

OLD_DIR="LexDocsPro-LITE-BACKUP-31ene-2244h"
NEW_DIR="LexDocsPro-LITE"

# Verificar que existen ambos directorios
if [ ! -d "$OLD_DIR" ]; then
    echo -e "${RED}❌ No se encuentra: $OLD_DIR${NC}"
    exit 1
fi

if [ ! -d "$NEW_DIR" ]; then
    echo -e "${RED}❌ No se encuentra: $NEW_DIR${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Ambas versiones encontradas${NC}"
echo ""

# FUNCIÓN: Contar archivos
count_files() {
    find "$1" -type f | wc -l | tr -d ' '
}

# FUNCIÓN: Obtener tamaño
get_size() {
    du -sh "$1" | cut -f1
}

# FUNCIÓN: Fecha de modificación de archivo
get_file_date() {
    if [ -f "$1/$2" ]; then
        stat -f "%Sm" -t "%Y-%m-%d %H:%M" "$1/$2" 2>/dev/null || echo "N/A"
    else
        echo "NO EXISTE"
    fi
}

# FUNCIÓN: Tamaño de archivo
get_file_size() {
    if [ -f "$1/$2" ]; then
        ls -lh "$1/$2" | awk '{print $5}'
    else
        echo "N/A"
    fi
}

# FUNCIÓN: Contar líneas
count_lines() {
    if [ -f "$1/$2" ]; then
        wc -l < "$1/$2" | tr -d ' '
    else
        echo "0"
    fi
}

echo "=============================================="
echo "📊 ESTADÍSTICAS GENERALES"
echo "=============================================="
echo ""

OLD_FILES=$(count_files "$OLD_DIR")
NEW_FILES=$(count_files "$NEW_DIR")
OLD_SIZE=$(get_size "$OLD_DIR")
NEW_SIZE=$(get_size "$NEW_DIR")

printf "%-30s %-20s %-20s\n" "MÉTRICA" "VERSIÓN ANTIGUA" "VERSIÓN NUEVA"
printf "%-30s %-20s %-20s\n" "$(printf '%.0s-' {1..30})" "$(printf '%.0s-' {1..20})" "$(printf '%.0s-' {1..20})"
printf "%-30s %-20s %-20s\n" "Total archivos:" "$OLD_FILES" "$NEW_FILES"
printf "%-30s %-20s %-20s\n" "Tamaño total:" "$OLD_SIZE" "$NEW_SIZE"

echo ""
echo "=============================================="
echo "📄 ARCHIVOS CRÍTICOS - COMPARACIÓN"
echo "=============================================="
echo ""

# Lista de archivos críticos
CRITICAL_FILES=(
    "run.py"
    "services/ai_service.py"
    "services/document_generator.py"
    "services/lexnet_analyzer.py"
    "services/ocr_service.py"
    "services/ollama_service.py"
    "static/js/app.js"
    "templates/index.html"
    "requirements.txt"
    ".env"
)

printf "%-35s %-20s %-20s %-20s %-20s\n" "ARCHIVO" "FECHA ANTIGUA" "FECHA NUEVA" "LÍNEAS ANT" "LÍNEAS NUE"
printf "%-35s %-20s %-20s %-20s %-20s\n" "$(printf '%.0s-' {1..35})" "$(printf '%.0s-' {1..20})" "$(printf '%.0s-' {1..20})" "$(printf '%.0s-' {1..20})" "$(printf '%.0s-' {1..20})"

for file in "${CRITICAL_FILES[@]}"; do
    OLD_DATE=$(get_file_date "$OLD_DIR" "$file")
    NEW_DATE=$(get_file_date "$NEW_DIR" "$file")
    OLD_LINES=$(count_lines "$OLD_DIR" "$file")
    NEW_LINES=$(count_lines "$NEW_DIR" "$file")
    
    # Colorear según diferencias
    if [ "$OLD_LINES" != "$NEW_LINES" ] && [ "$NEW_LINES" != "0" ] && [ "$OLD_LINES" != "0" ]; then
        printf "%-35s %-20s %-20s ${YELLOW}%-20s %-20s${NC}\n" "$file" "$OLD_DATE" "$NEW_DATE" "$OLD_LINES" "$NEW_LINES"
    else
        printf "%-35s %-20s %-20s %-20s %-20s\n" "$file" "$OLD_DATE" "$NEW_DATE" "$OLD_LINES" "$NEW_LINES"
    fi
done

echo ""
echo "=============================================="
echo "🔍 DIFERENCIAS EN SERVICES/"
echo "=============================================="
echo ""

# Comparar servicios
for service in ai_service.py document_generator.py lexnet_analyzer.py ocr_service.py ollama_service.py; do
    OLD_SERVICE="$OLD_DIR/services/$service"
    NEW_SERVICE="$NEW_DIR/services/$service"
    
    if [ -f "$OLD_SERVICE" ] && [ -f "$NEW_SERVICE" ]; then
        DIFF_COUNT=$(diff "$OLD_SERVICE" "$NEW_SERVICE" 2>/dev/null | wc -l | tr -d ' ')
        if [ "$DIFF_COUNT" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  $service: $DIFF_COUNT líneas diferentes${NC}"
        else
            echo -e "${GREEN}✅ $service: Idénticos${NC}"
        fi
    elif [ ! -f "$OLD_SERVICE" ]; then
        echo -e "${BLUE}🆕 $service: NUEVO en versión reciente${NC}"
    elif [ ! -f "$NEW_SERVICE" ]; then
        echo -e "${RED}❌ $service: FALTA en versión reciente${NC}"
    fi
done

echo ""
echo "=============================================="
echo "📦 ARCHIVOS ÚNICOS EN CADA VERSIÓN"
echo "=============================================="
echo ""

echo -e "${BLUE}🔹 Solo en VERSIÓN ANTIGUA:${NC}"
comm -23 <(cd "$OLD_DIR" && find . -type f | sort) <(cd "$NEW_DIR" && find . -type f | sort) | head -10

echo ""
echo -e "${BLUE}🔹 Solo en VERSIÓN NUEVA:${NC}"
comm -13 <(cd "$OLD_DIR" && find . -type f | sort) <(cd "$NEW_DIR" && find . -type f | sort) | head -10

echo ""
echo "=============================================="
echo "🎯 GIT - COMPARACIÓN DE COMMITS"
echo "=============================================="
echo ""

if [ -d "$OLD_DIR/.git" ] && [ -d "$NEW_DIR/.git" ]; then
    echo "Versión ANTIGUA:"
    cd "$OLD_DIR"
    git log --oneline -5 2>/dev/null || echo "  Sin commits o Git no inicializado"
    cd ..
    
    echo ""
    echo "Versión NUEVA:"
    cd "$NEW_DIR"
    git log --oneline -5 2>/dev/null || echo "  Sin commits o Git no inicializado"
    cd ..
else
    echo "Git no disponible en una o ambas versiones"
fi

echo ""
echo "=============================================="
echo "🔬 ANÁLISIS DETALLADO - run.py"
echo "=============================================="
echo ""

echo "Comparando run.py..."
if [ -f "$OLD_DIR/run.py" ] && [ -f "$NEW_DIR/run.py" ]; then
    DIFF_LINES=$(diff "$OLD_DIR/run.py" "$NEW_DIR/run.py" | grep "^[<>]" | head -20)
    if [ -n "$DIFF_LINES" ]; then
        echo -e "${YELLOW}Primeras 20 diferencias encontradas:${NC}"
        echo "$DIFF_LINES"
    else
        echo -e "${GREEN}✅ Archivos run.py son idénticos${NC}"
    fi
else
    echo -e "${RED}❌ run.py no encontrado en una de las versiones${NC}"
fi

echo ""
echo "=============================================="
echo "🔬 ANÁLISIS DETALLADO - app.js"
echo "=============================================="
echo ""

echo "Comparando app.js..."
if [ -f "$OLD_DIR/static/js/app.js" ] && [ -f "$NEW_DIR/static/js/app.js" ]; then
    OLD_APP_SIZE=$(get_file_size "$OLD_DIR" "static/js/app.js")
    NEW_APP_SIZE=$(get_file_size "$NEW_DIR" "static/js/app.js")
    OLD_APP_LINES=$(count_lines "$OLD_DIR" "static/js/app.js")
    NEW_APP_LINES=$(count_lines "$NEW_DIR" "static/js/app.js")
    
    echo "  Antigua: $OLD_APP_SIZE ($OLD_APP_LINES líneas)"
    echo "  Nueva:   $NEW_APP_SIZE ($NEW_APP_LINES líneas)"
    
    DIFF_COUNT=$(diff "$OLD_DIR/static/js/app.js" "$NEW_DIR/static/js/app.js" 2>/dev/null | wc -l | tr -d ' ')
    if [ "$DIFF_COUNT" -gt 0 ]; then
        echo -e "  ${YELLOW}⚠️  $DIFF_COUNT líneas diferentes${NC}"
    else
        echo -e "  ${GREEN}✅ Idénticos${NC}"
    fi
else
    echo -e "${RED}❌ app.js no encontrado en una de las versiones${NC}"
fi

echo ""
echo "=============================================="
echo "📋 RECOMENDACIÓN FINAL"
echo "=============================================="
echo ""

# Calcular puntuación
SCORE_OLD=0
SCORE_NEW=0

# Más archivos = mejor
if [ "$NEW_FILES" -gt "$OLD_FILES" ]; then
    SCORE_NEW=$((SCORE_NEW + 2))
elif [ "$OLD_FILES" -gt "$NEW_FILES" ]; then
    SCORE_OLD=$((SCORE_OLD + 2))
fi

# Versión más reciente = mejor (sabemos que NEW es más reciente)
SCORE_NEW=$((SCORE_NEW + 3))

# Archivos críticos presentes
for file in "${CRITICAL_FILES[@]}"; do
    [ -f "$OLD_DIR/$file" ] && SCORE_OLD=$((SCORE_OLD + 1))
    [ -f "$NEW_DIR/$file" ] && SCORE_NEW=$((SCORE_NEW + 1))
done

echo "Puntuación calculada:"
echo "  📦 Versión ANTIGUA (31/01 22:44): $SCORE_OLD puntos"
echo "  📦 Versión NUEVA (01/02 02:31):   $SCORE_NEW puntos"
echo ""

if [ "$SCORE_NEW" -gt "$SCORE_OLD" ]; then
    echo -e "${GREEN}✅ RECOMENDACIÓN: Usar VERSIÓN NUEVA${NC}"
    echo ""
    echo "Razones:"
    echo "  • Más reciente (~4 horas después)"
    echo "  • Probablemente incluye correcciones del 31/01"
    echo "  • Snapshot tomado después de las 22:44h"
else
    echo -e "${YELLOW}⚠️  RECOMENDACIÓN: Revisar manualmente${NC}"
    echo ""
    echo "Razones:"
    echo "  • Diferencias significativas detectadas"
    echo "  • Validar archivos críticos antes de decidir"
fi

echo ""
echo "=============================================="
echo "🔄 PRÓXIMOS PASOS SUGERIDOS"
echo "=============================================="
echo ""
echo "1. Revisar diferencias en archivos marcados en ${YELLOW}AMARILLO${NC}"
echo "2. Si decides usar VERSIÓN NUEVA:"
echo "   cd /Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE"
echo "   python3 -m venv venv"
echo "   source venv/bin/activate"
echo "   pip install -r requirements.txt"
echo "   python run.py"
echo ""
echo "3. Si decides usar VERSIÓN ANTIGUA:"
echo "   cd /Users/victormfrancisco/Desktop/PROYECTOS/LexDocsPro-LITE-BACKUP-31ene-2244h"
echo "   # Ya tiene venv activado"
echo ""

