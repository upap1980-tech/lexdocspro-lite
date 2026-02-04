#!/bin/bash
# =================================================================
# 🚀 LEXDOCSPRO LITE - SCRIPT UNIFICADO DE HOTFIX v2.3.2
# Fecha: 2026-02-04
# Propósito: Corregir DB Crash, Restaurar UI y Asegurar Endpoints
# =================================================================

set -e

echo "Starting Hotfix v2.3.2 implementation..."

# 1. BACKUP DE SEGURIDAD
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p _backups_/hotfix_${TIMESTAMP}
[ -f run.py ] && cp run.py _backups_/hotfix_${TIMESTAMP}/run.py.pre_hotfix
[ -f templates/index.html ] && cp templates/index.html _backups_/hotfix_${TIMESTAMP}/index.html.pre_hotfix
echo "✅ Backup created in _backups_/hotfix_${TIMESTAMP}"

# 2. FIX DATABASE CRASH & SEGURIDAD (Python Script para precisión)
echo "🔧 Patching run.py (DB Connections & JWT Security)..."
python3 -c "
import re

with open('run.py', 'r') as f:
    content = f.read()

# Fix 1: Eliminar db.conn.cursor() y usar context manager en dashboard_stats_detailed
dashboard_pattern = r'def dashboard_stats_detailed\(\):.*?return jsonify\(\{.*?\}\)'
dashboard_replacement = \"\"\"def dashboard_stats_detailed():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM saved_documents')
        docs_total = cursor.fetchone()[0]

        cursor.execute('''
            SELECT doc_type, COUNT(*) as count 
            FROM saved_documents 
            WHERE created_at >= DATE(\'now\', \'-30 days\')
            AND doc_type IS NOT NULL AND doc_type != \'\'
            GROUP BY doc_type 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        by_type_rows = cursor.fetchall()
        by_type = {row[0]: row[1] for row in by_type_rows}

        cursor.execute('''
            SELECT client_name, COUNT(*) as count 
            FROM saved_documents 
            WHERE created_at >= DATE(\'now\', \'-30 days\')
            AND client_name IS NOT NULL AND client_name != \'\'
            GROUP BY client_name 
            ORDER BY count DESC 
            LIMIT 10
        ''')
        by_client_rows = cursor.fetchall()
        by_client = {row[0]: row[1] for row in by_client_rows}

        return jsonify({
            'success': True,
            'stats': {
                'total_documents': docs_total,
                'by_type': by_type,
                'by_client': by_client
            }
        })
    except Exception as e:
        app.logger.error(f'DB Error: {str(e)}')
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()\"\"\"

# Aplicar el cambio al dashboard si coincide con la estructura
if 'def dashboard_stats_detailed():' in content:
    content = re.sub(r'def dashboard_stats_detailed\(\):.*?(?=\n\n|\n@)', dashboard_replacement, content, flags=re.DOTALL)

# Fix 2: Asegurar endpoints críticos con @jwt_required_custom
endpoints = ['smart_analyze_document', 'ocr_upload', 'lexnet_analyze']
for ep in endpoints:
    pattern = rf'@app\.route\(.*?\)\ndef {ep}'
    if rf'@jwt_required_custom\n@app.route' not in content:
        content = re.sub(rf'(@app\.route\(.*?\))\n(def {ep})', r'\1\n@jwt_required_custom\n\2', content)

with open('run.py', 'w') as f:
    f.write(content)
"
echo "✅ run.py patched successfully."

# 3. RESTAURACIÓN DE UI (index.html)
echo "🎨 Restoring Enterprise UI..."
if [ -f "_backups_/LexDocsPro Enterprise v3.0.html" ]; then
    cp "_backups_/LexDocsPro Enterprise v3.0.html" templates/index.html
    echo "✅ index.html restored to Enterprise v3.0"
elif [ -f "templates/index.html.backup.20260204" ]; then
    cp "templates/index.html.backup.20260204" templates/index.html
    echo "✅ index.html restored from local backup"
else
    echo "⚠️ Warning: No suitable index.html backup found. Manual restore required."
fi

# 4. LIMPIEZA DE CACHÉ
echo "🧹 Cleaning Python cache..."
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +
echo "✅ Cache cleaned."

# 5. VALIDACIÓN DE SINTAXIS
echo "🔍 Validating syntax..."
if python3 -m py_compile run.py; then
    echo "🟢 SUCCESS: Hotfix v2.3.2 applied. Syntax is valid."
    echo "👉 Run: pkill -f 'flask run' && flask run --port 5001"
else
    echo "🔴 ERROR: Syntax error detected in run.py. Reverting..."
    cp _backups_/hotfix_${TIMESTAMP}/run.py.pre_hotfix run.py
    exit 1
fi
