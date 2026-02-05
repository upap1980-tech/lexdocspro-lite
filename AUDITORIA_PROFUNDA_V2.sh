#!/bin/bash
# AUDITORIA_PROFUNDA_V2_COMPATIBLE.sh - Análisis exhaustivo LexDocsPro LITE
# Compatible con Bash 3.x (macOS) y Zsh
# Fecha: 05/02/2026 04:24 AM WET
# Versión: 2.1 - macOS Compatible Edition

cd ~/Desktop/PROYECTOS/LexDocsPro-LITE || { echo "❌ Directorio no encontrado"; exit 1; }

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m'

# Archivo de salida
REPORT_FILE="AUDITORIA_PROFUNDA_$(date +%Y%m%d_%H%M%S).md"

# Contadores
TOTAL=0
IMPLEMENTADO=0
PARCIAL=0
NO_IMPLEMENTADO=0

# Arrays simples (compatible Bash 3.x)
FUNC_IDS=()
FUNC_NOMBRES=()
FUNC_ESTADOS=()
FUNC_CONFIANZAS=()

# Inicio del reporte
{
cat <<EOF
# 🔍 AUDITORÍA PROFUNDA - LEXDOCSPRO LITE V2.0

**Fecha:** $(date '+%Y-%m-%d %H:%M:%S')
**Directorio:** $(pwd)
**Sistema:** $(uname -s) $(uname -r)
**Shell:** $SHELL
**Usuario:** $(whoami)

---

## 📋 METODOLOGÍA

Este análisis verifica **100+ funcionalidades** en 10 categorías:
1. Backend Python (servicios, OCR, IA)
2. Base de Datos SQLite (schema, tablas)
3. API REST (endpoints, seguridad)
4. Frontend JavaScript (componentes modulares)
5. Frontend HTML (templates, secciones)
6. Funcionalidades específicas
7. Tests automatizados
8. Configuración y dependencias
9. Estructura de carpetas
10. Análisis de código avanzado

---

EOF
} > "$REPORT_FILE"

# Función de logging
log_section() {
    {
        echo ""
        echo "═══════════════════════════════════════════════════════════════"
        echo "$1"
        echo "═══════════════════════════════════════════════════════════════"
        echo ""
    } >> "$REPORT_FILE"
}

log_subsection() {
    {
        echo ""
        echo "### $1"
        echo ""
    } >> "$REPORT_FILE"
}

# Función de verificación simplificada pero robusta
verificar() {
    TOTAL=$((TOTAL + 1))
    local id="$1"
    local nombre="$2"
    local tipo="$3"
    shift 3
    
    local resultado=""
    local estado="NO_IMPLEMENTADO"
    local confianza=0
    local mensaje=""
    
    case "$tipo" in
        "archivo")
            local ruta="$1"
            if [ -f "$ruta" ]; then
                local lineas=$(wc -l < "$ruta" 2>/dev/null || echo "0")
                estado="IMPLEMENTADO"
                confianza=100
                mensaje="✅ EXISTE ($lineas líneas)"
            elif [ -d "$ruta" ]; then
                local archivos=$(ls -1 "$ruta" 2>/dev/null | wc -l)
                estado="IMPLEMENTADO"
                confianza=100
                mensaje="✅ EXISTE ($archivos archivos)"
            else
                mensaje="❌ NO EXISTE"
            fi
            ;;
            
        "grep")
            local patron="$1"
            local archivo="$2"
            local minimo="${3:-1}"
            
            if [ -f "$archivo" ]; then
                local count=$(grep -c "$patron" "$archivo" 2>/dev/null || echo "0")
                if [ "$count" -ge "$minimo" ]; then
                    estado="IMPLEMENTADO"
                    confianza=90
                    mensaje="✅ ENCONTRADO ($count ocurrencias)"
                elif [ "$count" -gt 0 ]; then
                    estado="PARCIAL"
                    confianza=50
                    mensaje="🟡 PARCIAL ($count de $minimo)"
                else
                    mensaje="❌ NO ENCONTRADO"
                fi
            else
                mensaje="❌ Archivo no existe"
            fi
            ;;
            
        "conteo")
            local comando="$1"
            local min="$2"
            local max="${3:-999}"
            
            resultado=$(eval "$comando" 2>/dev/null || echo "0")
            
            if [ "$resultado" -ge "$min" ] && [ "$resultado" -le "$max" ]; then
                estado="IMPLEMENTADO"
                confianza=95
                mensaje="✅ OK ($resultado)"
            elif [ "$resultado" -gt 0 ]; then
                estado="PARCIAL"
                confianza=40
                mensaje="🟡 PARCIAL ($resultado de $min-$max)"
            else
                mensaje="❌ NO ($resultado)"
            fi
            ;;
            
        "sql")
            local db="$1"
            local query="$2"
            
            if [ -f "$db" ]; then
                resultado=$(sqlite3 "$db" "$query" 2>/dev/null || echo "0")
                if [ "$resultado" -ge 1 ]; then
                    estado="IMPLEMENTADO"
                    confianza=100
                    mensaje="✅ EXISTE"
                else
                    mensaje="❌ NO EXISTE"
                fi
            else
                mensaje="❌ BD no existe"
            fi
            ;;
    esac
    
    # Guardar en arrays
    FUNC_IDS+=("$id")
    FUNC_NOMBRES+=("$nombre")
    FUNC_ESTADOS+=("$estado")
    FUNC_CONFIANZAS+=("$confianza")
    
    # Actualizar contadores
    case "$estado" in
        "IMPLEMENTADO") IMPLEMENTADO=$((IMPLEMENTADO + 1)) ;;
        "PARCIAL") PARCIAL=$((PARCIAL + 1)) ;;
        *) NO_IMPLEMENTADO=$((NO_IMPLEMENTADO + 1)) ;;
    esac
    
    # Escribir resultado
    {
        echo "**[$TOTAL] $nombre**"
        echo "  $mensaje"
        echo ""
    } >> "$REPORT_FILE"
}

# ═══════════════════════════════════════════════════════════════
# AUDITORÍA COMPLETA
# ═══════════════════════════════════════════════════════════════

log_section "1️⃣ BACKEND - SERVICIOS PYTHON"

log_subsection "1.1 Servicio OCR"
verificar "F01" "Archivo services/ocrservice.py" "archivo" "services/ocrservice.py"
verificar "F02" "Función extract_text()" "grep" "def extract_text" "services/ocrservice.py" 1
verificar "F03" "Integración Tesseract" "grep" "pytesseract\|tesseract" "services/ocrservice.py" 1
verificar "F04" "Integración pdf2image" "grep" "pdf2image\|convert_from_path" "services/ocrservice.py" 1

log_subsection "1.2 Servicio IA Multi-Modelo"
verificar "F05" "Archivo services/aiservice.py" "archivo" "services/aiservice.py"
verificar "F06" "Integración Ollama" "grep" "ollama\|localhost:11434" "services/aiservice.py" 1
verificar "F07" "Integración Groq" "grep" "groq\|GROQ" "services/aiservice.py" 1
verificar "F08" "Integración Perplexity" "grep" "perplexity\|PERPLEXITY" "services/aiservice.py" 1
verificar "F09" "Función consultar IA" "grep" "def.*consultar\|def.*chat\|def.*query" "services/aiservice.py" 1

log_subsection "1.3 Generador de Documentos"
verificar "F10" "Archivo services/documentgenerator.py" "archivo" "services/documentgenerator.py"
verificar "F11" "Funciones generate_* (conteo)" "conteo" "grep -c '^def generate_' services/documentgenerator.py 2>/dev/null || echo 0" 10 12
verificar "F12" "Demanda Civil" "grep" "generate_demanda_civil\|demanda.*civil" "services/documentgenerator.py" 1
verificar "F13" "Recurso Apelación" "grep" "generate_recurso_apelacion\|recurso.*apelac" "services/documentgenerator.py" 1
verificar "F14" "Acta Conciliación" "grep" "generate_acta_conciliacion\|acta.*concilia" "services/documentgenerator.py" 1

log_subsection "1.4 Analizador LexNET"
verificar "F15" "Archivo services/lexnetanalyzer.py" "archivo" "services/lexnetanalyzer.py"
verificar "F16" "Función análisis notificación" "grep" "def.*analiz\|def.*parse" "services/lexnetanalyzer.py" 1
verificar "F17" "Cálculo de plazos" "grep" "dias.*plazo\|deadline\|vencimiento" "services/lexnetanalyzer.py" 1
verificar "F18" "Calendario festivos 2026" "grep" "FESTIVOS.*2026\|holidays.*2026" "services/lexnetanalyzer.py" 1

log_subsection "1.5 Servicio de Archivos"
verificar "F19" "Archivo services/fileservice.py" "archivo" "services/fileservice.py"
verificar "F20" "Función list_directory()" "grep" "def list_directory\|def browse\|def list_files" "services/fileservice.py" 1

log_section "2️⃣ BASE DE DATOS - SQLITE"

verificar "F21" "Base de datos legaldocs.db" "archivo" "instance/legaldocs.db"

if [ -f "instance/legaldocs.db" ]; then
    log_subsection "2.1 Tablas Principales"
    verificar "F22" "Tabla users" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='users'"
    verificar "F23" "Tabla pending_documents" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='pending_documents'"
    verificar "F24" "Tabla saved_documents" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='saved_documents'"
    verificar "F25" "Tabla clients" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='clients'"
    verificar "F26" "Tabla cases" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='cases'"
    verificar "F27" "Tabla audit_log" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='audit_log'"
    verificar "F28" "Tabla token_blacklist" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='token_blacklist'"
    verificar "F29" "Tabla notifications" "sql" "instance/legaldocs.db" "SELECT COUNT(*) FROM sqlite_master WHERE type='table' AND name='notifications'"
else
    {
        echo "⚠️  **Base de datos no encontrada** - Saltando verificación de tablas"
        echo ""
    } >> "$REPORT_FILE"
fi

log_section "3️⃣ API REST - ENDPOINTS"

verificar "F30" "Archivo run.py" "archivo" "run.py"
verificar "F31" "Tamaño run.py (líneas)" "conteo" "wc -l < run.py 2>/dev/null || echo 0" 300 2000

log_subsection "3.1 Endpoints Core"
verificar "F32" "Endpoint POST /login" "grep" "@app.route.*login.*POST\|@app.route.*login" "run.py" 1
verificar "F33" "Endpoint /api/dashboard/stats" "grep" "@app.route.*dashboard.*stats" "run.py" 1
verificar "F34" "Endpoint /api/ocr/upload" "grep" "@app.route.*ocr.*upload" "run.py" 1
verificar "F35" "Endpoint /api/document/smart-analyze" "grep" "@app.route.*document.*smart\|@app.route.*document.*propose\|@app.route.*document.*analyze" "run.py" 1
verificar "F36" "Endpoint /api/lexnet/analyze" "grep" "@app.route.*lexnet.*analyz" "run.py" 1
verificar "F37" "Endpoint /api/clientes" "grep" "@app.route.*clientes\|@app.route.*clients" "run.py" 1
verificar "F38" "Endpoint /api/files" "grep" "@app.route.*files\|@app.route.*browse" "run.py" 1
verificar "F39" "Endpoint PDF viewer" "grep" "@app.route.*pdf.*filename\|send_file.*pdf" "run.py" 1
verificar "F40" "Total endpoints" "conteo" "grep -c '@app.route' run.py 2>/dev/null || echo 0" 15 50

log_section "4️⃣ SEGURIDAD - JWT"

verificar "F41" "Import FlaskJWTExtended" "grep" "from flask_jwt_extended import\|import flask_jwt_extended" "run.py" 1
verificar "F42" "JWT_SECRET_KEY configurado" "grep" "JWT_SECRET_KEY\|jwt.*secret" "run.py" 1
verificar "F43" "JWTManager inicializado" "grep" "JWTManager.*app\|jwt.*=.*JWT" "run.py" 1
verificar "F44" "Decoradores @jwt_required" "conteo" "grep -c '@jwt_required' run.py 2>/dev/null || echo 0" 5 30
verificar "F45" "Archivo decorators.py" "archivo" "decorators.py"

log_section "5️⃣ FRONTEND - JAVASCRIPT"

verificar "F46" "Archivo static/js/app.js" "archivo" "static/js/app.js"
verificar "F47" "Tamaño app.js" "conteo" "wc -l < static/js/app.js 2>/dev/null || echo 0" 500 5000

log_subsection "5.1 Componentes Modulares"
verificar "F48" "document-confirm-modal.js" "archivo" "static/js/document-confirm-modal.js"
verificar "F49" "file-explorer.js" "archivo" "static/js/file-explorer.js"
verificar "F50" "pdf-viewer.js" "archivo" "static/js/pdf-viewer.js"
verificar "F51" "ai-chat.js" "archivo" "static/js/ai-chat.js"
verificar "F52" "dashboard.js" "archivo" "static/js/dashboard.js"
verificar "F53" "document-generator.js" "archivo" "static/js/document-generator.js"

if [ -f "static/js/app.js" ]; then
    log_subsection "5.2 Funcionalidades JS"
    verificar "F54" "Fetch API calls" "conteo" "grep -c 'fetch.*api\|fetch.*http' static/js/app.js 2>/dev/null || echo 0" 5 50
    verificar "F55" "Event listeners" "conteo" "grep -c 'addEventListener\|onclick' static/js/app.js 2>/dev/null || echo 0" 10 100
fi

log_section "6️⃣ FRONTEND - HTML"

verificar "F56" "Archivo templates/index.html" "archivo" "templates/index.html"
verificar "F57" "Tamaño index.html" "conteo" "wc -l < templates/index.html 2>/dev/null || echo 0" 200 1000

if [ -f "templates/index.html" ]; then
    log_subsection "6.1 Secciones (15 módulos)"
    verificar "F58" "Sección Dashboard" "grep" "<section.*id=[\"']dashboard" "templates/index.html" 1
    verificar "F59" "Sección Expedientes" "grep" "<section.*id=[\"']expedientes" "templates/index.html" 1
    verificar "F60" "Sección LexNET" "grep" "<section.*id=[\"']lexnet" "templates/index.html" 1
    verificar "F61" "Sección IA Cascade" "grep" "<section.*id=[\"']ia-cascade" "templates/index.html" 1
    verificar "F62" "Sección Autoprocesos" "grep" "<section.*id=[\"']autoprocesos" "templates/index.html" 1
    verificar "F63" "Total secciones (15)" "conteo" "grep -c '<section.*id=' templates/index.html 2>/dev/null || echo 0" 15 20
    verificar "F64" "Sidebar navegación" "grep" "sidebar\|nav-item" "templates/index.html" 10
fi

log_section "7️⃣ FUNCIONALIDADES ESPECÍFICAS"

log_subsection "7.1 Watchdog / Autoprocesamiento"
verificar "F65" "Script autoprocesar.py" "archivo" "autoprocesar.py"
if [ -f "autoprocesar.py" ]; then
    verificar "F66" "Watchdog Observer" "grep" "Observer\|watchdog\|FileSystemEventHandler" "autoprocesar.py" 1
fi

log_subsection "7.2 Templates Legales"
verificar "F67" "Carpeta templates/legal" "archivo" "templates/legal"
if [ -d "templates/legal" ]; then
    verificar "F68" "Templates .md legales" "conteo" "ls -1 templates/legal/*.md 2>/dev/null | wc -l" 1 15
fi
verificar "F69" "Template acta_conciliacion.md" "archivo" "templates/legal/acta_conciliacion.md"

log_subsection "7.3 Tests"
verificar "F70" "Carpeta tests/" "archivo" "tests"
if [ -d "tests" ]; then
    verificar "F71" "Scripts de test .sh" "conteo" "ls -1 tests/*.sh 2>/dev/null | wc -l" 1 10
    verificar "F72" "test_master_suite.sh" "archivo" "tests/test_master_suite.sh"
fi

log_subsection "7.4 Estilos CSS"
verificar "F73" "Archivo static/css/style.css" "archivo" "static/css/style.css"
if [ -f "static/css/style.css" ]; then
    verificar "F74" "Media queries responsive" "conteo" "grep -c '@media' static/css/style.css 2>/dev/null || echo 0" 3 20
    verificar "F75" "Dark mode" "grep" "dark.*mode\|theme.*dark\|\.dark" "static/css/style.css" 1
fi

log_section "8️⃣ CONFIGURACIÓN"

verificar "F76" "requirements.txt" "archivo" "requirements.txt"
if [ -f "requirements.txt" ]; then
    verificar "F77" "Flask" "grep" "Flask" "requirements.txt" 1
    verificar "F78" "flask-jwt-extended" "grep" "flask-jwt-extended" "requirements.txt" 1
    verificar "F79" "PyPDF2" "grep" "PyPDF2" "requirements.txt" 1
    verificar "F80" "pytesseract" "grep" "pytesseract" "requirements.txt" 1
fi

verificar "F81" ".env.example" "archivo" ".env.example"
verificar "F82" "config.py" "archivo" "config.py"
verificar "F83" "README.md" "archivo" "README.md"

log_section "9️⃣ ESTRUCTURA"

verificar "F84" "Carpeta services/" "archivo" "services"
verificar "F85" "Carpeta static/" "archivo" "static"
verificar "F86" "Carpeta templates/" "archivo" "templates"
verificar "F87" "Carpeta instance/" "archivo" "instance"
verificar "F88" "Entorno virtual (.venv o venv)" "conteo" "ls -d .venv* venv 2>/dev/null | wc -l" 1 2

log_section "🔍 ANÁLISIS AVANZADO"

if [ -f "run.py" ]; then
    log_subsection "10.1 Métricas de Código"
    verificar "F89" "Patrón db.get_connection()" "grep" "db\.get_connection\|get_connection()" "run.py" 3
    verificar "F90" "Bloques try-except" "conteo" "grep -c 'try:' run.py 2>/dev/null || echo 0" 10 50
    verificar "F91" "Logging implementado" "grep" "logger\|logging\|app\.logger" "run.py" 5
    verificar "F92" "TODOs pendientes" "conteo" "grep -ri 'TODO\|FIXME' . --include='*.py' --exclude-dir='.venv*' --exclude-dir='venv' 2>/dev/null | wc -l" 0 10
fi

# ═══════════════════════════════════════════════════════════════
# RESUMEN FINAL
# ═══════════════════════════════════════════════════════════════

{
    echo ""
    echo "═══════════════════════════════════════════════════════════════"
    echo "📊 RESUMEN EJECUTIVO FINAL"
    echo "═══════════════════════════════════════════════════════════════"
    echo ""
    echo "## Estadísticas Generales"
    echo ""
    echo "| Métrica | Valor |"
    echo "|---------|-------|"
    echo "| **Total funcionalidades** | $TOTAL |"
    echo "| ✅ **Implementadas** | $IMPLEMENTADO ($(( IMPLEMENTADO * 100 / TOTAL ))%) |"
    echo "| 🟡 **Parciales** | $PARCIAL ($(( PARCIAL * 100 / TOTAL ))%) |"
    echo "| ❌ **NO implementadas** | $NO_IMPLEMENTADO ($(( NO_IMPLEMENTADO * 100 / TOTAL ))%) |"
    echo ""
    
    PORCENTAJE_REAL=$(( (IMPLEMENTADO * 100 + PARCIAL * 50) / TOTAL ))
    
    echo "### 🎯 Implementación Real: **$PORCENTAJE_REAL%**"
    echo ""
    
    if [ $PORCENTAJE_REAL -ge 80 ]; then
        echo "✅ **EXCELENTE**: Sistema production-ready (≥80%)"
    elif [ $PORCENTAJE_REAL -ge 60 ]; then
        echo "⚠️ **BUENO**: Sistema funcional (60-79%)"
    elif [ $PORCENTAJE_REAL -ge 40 ]; then
        echo "⚠️ **REGULAR**: Funcionalidades básicas (40-59%)"
    else
        echo "🚨 **CRÍTICO**: Implementación insuficiente (<40%)"
    fi
    
    echo ""
    echo "---"
    echo ""
    
    # Tabla detallada
    echo "## Detalle por Funcionalidad"
    echo ""
    echo "| ID | Funcionalidad | Estado |"
    echo "|----|---------------|--------|"
    
    i=0
    while [ $i -lt ${#FUNC_IDS[@]} ]; do
        id="${FUNC_IDS[$i]}"
        nombre="${FUNC_NOMBRES[$i]}"
        estado="${FUNC_ESTADOS[$i]}"
        
        case "$estado" in
            "IMPLEMENTADO") icono="✅" ;;
            "PARCIAL") icono="🟡" ;;
            *) icono="❌" ;;
        esac
        
        printf "| %-6s | %-50s | %s %-15s |\n" "$id" "$nombre" "$icono" "$estado"
        i=$((i + 1))
    done
    
    echo ""
    echo "---"
    echo ""
    
    echo "## 🎯 Próximos Pasos"
    echo ""
    
    if [ $PORCENTAJE_REAL -lt 50 ]; then
        cat <<'EOFR'
### 🚨 ACCIÓN INMEDIATA

**Prioridades:**
1. Verificar si existe backup de versión funcional
2. Revisar repositorio GitHub para comparar
3. Restaurar servicios backend faltantes
4. Recrear base de datos con schema correcto

**Comandos sugeridos:**
```bash
# Revisar Git
git log --oneline --all | head -20
git status

# Buscar backups
find . -name "*.backup*" -o -name "*backup*" 2>/dev/null

# Comparar con GitHub
git remote -v
git fetch --all
git diff origin/main
