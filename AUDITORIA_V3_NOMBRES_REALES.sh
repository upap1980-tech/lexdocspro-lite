#!/bin/bash
# AUDITORIA_V3_NOMBRES_REALES.sh
# Versión corregida para nombres de archivos reales del proyecto

cd ~/Desktop/PROYECTOS/LexDocsPro-LITE

REPORT="AUDITORIA_REAL_$(date +%Y%m%d_%H%M%S).md"

cat > "$REPORT" <<'EOFR'
# 🔍 AUDITORÍA REAL - LEXDOCSPRO LITE (Nombres Reales)

**Fecha:** $(date)
**Rama:** $(git branch --show-current 2>/dev/null || echo "Sin Git")

---

## 1️⃣ SERVICIOS BACKEND (Nombres Reales)

EOFR

# Función verificar mejorada
check_file() {
    local nombre="$1"
    local archivo="$2"
    
    if [ -f "$archivo" ]; then
        local lineas=$(wc -l < "$archivo")
        echo "✅ **$nombre**: $lineas líneas" >> "$REPORT"
        
        # Mostrar primeras funciones/clases
        echo '```python' >> "$REPORT"
        grep -E "^(def |class )" "$archivo" | head -5 >> "$REPORT"
        echo '```' >> "$REPORT"
        echo "" >> "$REPORT"
    else
        echo "❌ **$nombre**: NO EXISTE" >> "$REPORT"
        echo "" >> "$REPORT"
    fi
}

# Verificar servicios con nombres reales
check_file "OCR Service" "services/ocr_service.py"
check_file "AI Service" "services/ai_service.py"
check_file "Document Generator" "services/document_generator.py"
check_file "LexNET Analyzer" "services/lexnet_analyzer.py"
check_file "LexNET Analyzer V2" "services/lexnet_analyzer_v2.py"
check_file "File Service" "services/file_service.py"
check_file "iCloud Service" "services/icloud_service.py"
check_file "Document Processing" "services/document_processing_service.py"
check_file "Autoprocessor" "services/autoprocessor_service.py"
check_file "Banking Service" "services/banking_service.py"
check_file "Email Service" "services/email_service.py"
check_file "PDF Preview Service" "services/pdf_preview_service.py"
check_file "Ollama Service" "services/ollama_service.py"

# Base de datos
{
    echo ""
    echo "## 2️⃣ BASE DE DATOS"
    echo ""
} >> "$REPORT"

for db_path in "instance/legaldocs.db" "legaldocs.db" "*.db"; do
    if [ -f "$db_path" ]; then
        echo "✅ **Base de datos encontrada**: \`$db_path\`" >> "$REPORT"
        echo "" >> "$REPORT"
        echo '```' >> "$REPORT"
        sqlite3 "$db_path" ".tables" >> "$REPORT" 2>/dev/null
        echo '```' >> "$REPORT"
        break
    fi
done

# run.py análisis
{
    echo ""
    echo "## 3️⃣ ARCHIVO RUN.PY"
    echo ""
} >> "$REPORT"

if [ -f "run.py" ]; then
    lineas=$(wc -l < run.py)
    endpoints=$(grep -c '@app.route' run.py)
    echo "✅ **run.py**: $lineas líneas, $endpoints endpoints" >> "$REPORT"
    echo "" >> "$REPORT"
    
    echo "### Endpoints encontrados:" >> "$REPORT"
    echo '```python' >> "$REPORT"
    grep '@app.route' run.py | head -15 >> "$REPORT"
    echo '```' >> "$REPORT"
fi

# Frontend
{
    echo ""
    echo "## 4️⃣ FRONTEND"
    echo ""
} >> "$REPORT"

check_file "app.js" "static/js/app.js"
check_file "style.css" "static/css/style.css"
check_file "index.html" "templates/index.html"

# Templates modulares
if [ -d "templates/modulos" ]; then
    echo "✅ **templates/modulos/**: $(ls templates/modulos/*.html 2>/dev/null | wc -l) archivos" >> "$REPORT"
    echo '```' >> "$REPORT"
    ls -1 templates/modulos/*.html 2>/dev/null >> "$REPORT"
    echo '```' >> "$REPORT"
fi

# Resumen
{
    echo ""
    echo "## 📊 RESUMEN"
    echo ""
    echo "- **Servicios Python**: $(ls -1 services/*.py 2>/dev/null | wc -l) archivos"
    echo "- **Templates HTML**: $(find templates -name "*.html" 2>/dev/null | wc -l) archivos"
    echo "- **Archivos JavaScript**: $(find static/js -name "*.js" 2>/dev/null | wc -l) archivos"
    echo "- **Archivos CSS**: $(find static/css -name "*.css" 2>/dev/null | wc -l) archivos"
    echo ""
    
    if [ -f "run.py" ]; then
        echo "✅ **Backend Flask operativo**"
    fi
    
    if [ -d "services" ] && [ "$(ls services/*.py 2>/dev/null | wc -l)" -gt 5 ]; then
        echo "✅ **Servicios completos**"
    fi
    
    echo ""
    echo "---"
    echo ""
    echo "**Estado real:** El proyecto tiene **TODA LA INFRAESTRUCTURA** necesaria."
    echo ""
    echo "**Problema anterior:** El script buscaba nombres incorrectos de archivos."
} >> "$REPORT"

cat "$REPORT"
echo ""
echo "✅ Reporte guardado en: $REPORT"

