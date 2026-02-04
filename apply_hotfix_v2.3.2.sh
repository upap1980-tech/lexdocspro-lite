#!/bin/bash
# =================================================================
# 🚀 LEXDOCSPRO LITE - SCRIPT UNIFICADO DE HOTFIX v2.3.2
# =================================================================

set -e
echo "Iniciando implementación de Hotfix v2.3.2..."

# 1. BACKUP
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p _backups_/hotfix_${TIMESTAMP}
cp run.py _backups_/hotfix_${TIMESTAMP}/run.py.pre_hotfix
cp templates/index.html _backups_/hotfix_${TIMESTAMP}/index.html.pre_hotfix
echo "✅ Backup creado en _backups_/hotfix_${TIMESTAMP}"

# 2. PARCHE run.py (DB & Seguridad)
echo "🔧 Parcheando run.py..."
python3 -c "
import re
with open('run.py', 'r') as f: content = f.read()

# Fix DB Dashboard
dash_replacement = '''def dashboard_stats_detailed():
    conn = None
    try:
        conn = db.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM saved_documents')
        docs_total = cursor.fetchone()[0]
        cursor.execute('SELECT doc_type, COUNT(*) as count FROM saved_documents WHERE created_at >= DATE(\"now\", \"-30 days\") AND doc_type IS NOT NULL AND doc_type != \"\" GROUP BY doc_type ORDER BY count DESC LIMIT 10')
        by_type_rows = cursor.fetchall()
        by_type = {row[0]: row[1] for row in by_type_rows}
        cursor.execute('SELECT client_name, COUNT(*) as count FROM saved_documents WHERE created_at >= DATE(\"now\", \"-30 days\") AND client_name IS NOT NULL AND client_name != \"\" GROUP BY client_name ORDER BY count DESC LIMIT 10')
        by_client_rows = cursor.fetchall()
        by_client = {row[0]: row[1] for row in by_client_rows}
        return jsonify({'success': True, 'stats': {'total_documents': docs_total, 'by_type': by_type, 'by_client': by_client}})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    finally:
        if conn: conn.close()'''

content = re.sub(r'def dashboard_stats_detailed\(\):.*?(?=\n\n|\n@)', dash_replacement, content, flags=re.DOTALL)

# Fix Seguridad Endpoints
for ep in ['smart_analyze_document', 'ocr_upload', 'lexnet_analyze']:
    if ep in content and '@jwt_required_custom' not in content.split(f'def {ep}')[0].split('@app.route')[-1]:
        content = re.sub(rf'(@app\.route\(.*?\))\n(def {ep})', r'\1\n@jwt_required_custom\n\2', content)

with open('run.py', 'w') as f: f.write(content)
"
echo "✅ run.py parcheado."

# 3. UI RESTORE
echo "🎨 Restaurando UI..."
if [ -f "templates/index.html.backup.20260204" ]; then
    cp "templates/index.html.backup.20260204" templates/index.html
    echo "✅ index.html restaurado."
else
    echo "⚠️ No se encontró backup de index.html, omitiendo..."
fi

# 4. LIMPIEZA
find . -name "*.pyc" -delete
find . -name "__pycache__" -exec rm -rf {} +
echo "✅ Caché limpia."

# 5. VALIDACIÓN
if python3 -m py_compile run.py; then
    echo "🟢 ÉXITO: Hotfix v2.3.2 aplicado. Sintaxis válida."
else
    echo "🔴 ERROR: Fallo en sintaxis. Restaurando backup..."
    cp _backups_/hotfix_${TIMESTAMP}/run.py.pre_hotfix run.py
    exit 1
fi
