#!/usr/bin/env bash
#
# setup_lexdocs.sh
# Automatiza Fase 1 y Fase 2 del sistema de Gestión Legal (backend Flask + frontend React)
# sin romper ni sobrescribir el código existente y sin perder funcionalidades.

set -euo pipefail

# ============= CONFIGURACIÓN BÁSICA =============

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/_backups_lexdocs_$(date +%Y%m%d_%H%M%S)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
NODE_BIN="${NODE_BIN:-node}"
NPM_BIN="${NPM_BIN:-npm}"

echo "==============================================="
echo "  SETUP LEXDOCS - FASE 1 + FASE 2 (AUTO)"
echo "==============================================="
echo "Proyecto:      ${PROJECT_ROOT}"
echo "Backup dir:    ${BACKUP_DIR}"
echo

mkdir -p "${BACKUP_DIR}"

backup_file() {
  local file="$1"
  if [[ -f "${file}" ]]; then
    local rel
    rel=$(realpath --relative-to="${PROJECT_ROOT}" "${file}" 2>/dev/null || echo "${file}")
    local dest="${BACKUP_DIR}/${rel}"
    mkdir -p "$(dirname "${dest}")"
    cp -p "${file}" "${dest}"
    echo "  [BACKUP] ${rel} → ${dest}"
  fi
}

ensure_python_venv() {
  echo "==> [FASE 1] Comprobando entorno Python / venv..."
  if [[ -d "${PROJECT_ROOT}/.venv" ]]; then
    echo "  venv existente encontrado en .venv"
  else
    echo "  Creando venv en .venv ..."
    "${PYTHON_BIN}" -m venv "${PROJECT_ROOT}/.venv"
  fi

  # shellcheck disable=SC1091
  source "${PROJECT_ROOT}/.venv/bin/activate"

  echo "==> [FASE 1] Instalando dependencias Python (si faltan)..."
  if [[ -f "${PROJECT_ROOT}/requirements.txt" ]]; then
    pip install --upgrade pip >/dev/null
    pip install -r "${PROJECT_ROOT}/requirements.txt"
  else
    echo "  [AVISO] No se encontró requirements.txt, omitiendo instalación de dependencias."
  fi
}

ensure_react_frontend() {
  echo
  echo "==> [FASE 2] Comprobando frontend React..."
  FRONT_DIR="${PROJECT_ROOT}/frontend"

  if [[ -d "${FRONT_DIR}" ]]; then
    echo "  Carpeta frontend existente: ${FRONT_DIR}"
  else
    echo "  [CREANDO] Estructura básica de frontend React en ${FRONT_DIR}"
    mkdir -p "${FRONT_DIR}"
    pushd "${FRONT_DIR}" >/dev/null
    "${NPM_BIN}" init -y
    "${NPM_BIN}" install react react-dom
    mkdir -p src
    cat > src/index.js <<'EOF'
import React from "react";
import { createRoot } from "react-dom/client";

const App = () => (
  <div style={{ padding: "16px", fontFamily: "system-ui" }}>
    <h1>LexDocs Auto-Procesador</h1>
    <p>Frontend básico inicializado. Sustituir por implementación real.</p>
  </div>
);

const container = document.getElementById("root");
const root = createRoot(container);
root.render(<App />);
EOF
    cat > index.html <<'EOF'
<!doctype html>
<html lang="es">
  <head>
    <meta charset="utf-8" />
    <title>LexDocs</title>
  </head>
  <body>
    <div id="root"></div>
    <script src="./src/index.js" type="module"></script>
  </body>
</html>
EOF
    popd >/dev/null
  fi

  echo "==> [FASE 2] Instalando dependencias frontend (si faltan package.json)..."
  if [[ -f "${FRONT_DIR}/package.json" ]]; then
    pushd "${FRONT_DIR}" >/dev/null
    "${NPM_BIN}" install
    popd >/dev/null
  else
    echo "  [AVISO] No se encontró package.json en frontend, se asume que ya está configurado manualmente."
  fi
}

ensure_python_services() {
  echo
  echo "==> [FASE 1] Verificando servicios Python mínimos..."

  mkdir -p "${PROJECT_ROOT}/services"

  # db_service.py mínimo (si no existe)
  if [[ ! -f "${PROJECT_ROOT}/services/db_service.py" ]]; then
    echo "  [CREANDO] services/db_service.py (stub mínimo, NO pisa nada existente)"
    cat > "${PROJECT_ROOT}/services/db_service.py" <<'EOF'
import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "lexdocs.db")

class DatabaseService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo_original TEXT,
            ruta_temporal TEXT,
            cliente_codigo TEXT,
            cliente_detectado TEXT,
            tipo_documento TEXT,
            fecha_documento TEXT,
            estado TEXT,
            ruta_definitiva TEXT,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nivel TEXT,
            origen TEXT,
            mensaje TEXT,
            documento_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        conn.close()

    def registrar_log(self, nivel, origen, mensaje, documento_id=None):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (nivel, origen, mensaje, documento_id) VALUES (?, ?, ?, ?)",
            (nivel, origen, mensaje, documento_id),
        )
        conn.commit()
        conn.close()

    # Métodos usados por los endpoints de Fase 2 (stubs seguros):

    def obtener_estadisticas_hoy(self):
        conn = self._get_conn()
        cur = conn.cursor()
        hoy = datetime.now().date().isoformat()
        cur.execute("SELECT COUNT(*) FROM documentos WHERE date(creado_en)=?", (hoy,))
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documentos WHERE estado='auto'")
        automaticos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documentos WHERE estado='revision'")
        en_revision = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documentos WHERE estado='error'")
        errores = cur.fetchone()[0]
        conn.close()
        return {
            "total_hoy": total,
            "automaticos": automaticos,
            "en_revision": en_revision,
            "errores": errores,
        }

    def obtener_cola_revision(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM documentos WHERE estado='revision' ORDER BY creado_en DESC")
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        conn.close()
        return rows

    def obtener_procesados_hoy(self):
        conn = self._get_conn()
        cur = conn.cursor()
        hoy = datetime.now().date().isoformat()
        cur.execute(
            "SELECT * FROM documentos WHERE date(creado_en)=? ORDER BY creado_en DESC",
            (hoy,),
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        conn.close()
        return rows

    def obtener_documento(self, doc_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM documentos WHERE id=?", (doc_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        cols = [c[0] for c in cur.description]
        conn.close()
        return dict(zip(cols, row))

    def actualizar_documento(self, doc_id: int, updates: dict):
        if not updates:
            return
        conn = self._get_conn()
        cur = conn.cursor()
        sets = ", ".join([f"{k}=?" for k in updates.keys()])
        values = list(updates.values()) + [doc_id]
        cur.execute(f"UPDATE documentos SET {sets} WHERE id=?", values)
        conn.commit()
        conn.close()

    def aprobar_documento(self, doc_id: int, ruta_definitiva: str, usuario_modifico: bool):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE documentos SET estado='auto', ruta_definitiva=? WHERE id=?",
            (ruta_definitiva, doc_id),
        )
        conn.commit()
        conn.close()

    def rechazar_documento(self, doc_id: int, motivo: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE documentos SET estado='rechazado' WHERE id=?",
            (doc_id,),
        )
        conn.commit()
        conn.close()
EOF
  else
    echo "  services/db_service.py ya existe, no se modifica."
  fi

  # decision_engine.py mínimo (si no existe)
  if [[ ! -f "${PROJECT_ROOT}/services/decision_engine.py" ]]; then
    echo "  [CREANDO] services/decision_engine.py (stub mínimo, NO pisa nada existente)"
    cat > "${PROJECT_ROOT}/services/decision_engine.py" <<'EOF'
import os
from datetime import datetime

class DecisionEngine:
    def __init__(self):
        pass

    def construir_ruta_destino(self, analisis: dict, base_dir: str):
        """
        Construye la ruta destino a partir del análisis:
        - cliente_codigo
        - tipo_documento
        - fecha_documento
        - archivo_original
        """
        cliente = analisis.get("cliente_codigo") or "SIN_CLIENTE"
        tipo = analisis.get("tipo_documento") or "SIN_TIPO"
        fecha_str = analisis.get("fecha_documento") or datetime.now().strftime("%Y%m%d")
        nombre = analisis.get("archivo_original") or "documento.pdf"

        # Estructura: BASE_DIR/cliente/tipo/AAAA/MM/
        ano = fecha_str[:4]
        mes = fecha_str[4:6] if len(fecha_str) >= 6 else "01"

        carpeta_cliente = os.path.join(base_dir, cliente)
        carpeta_tipo = os.path.join(carpeta_cliente, tipo)
        carpeta_fecha = os.path.join(carpeta_tipo, f"{ano}_{mes}")
        os.makedirs(carpeta_fecha, exist_ok=True)

        ruta_completa = os.path.join(carpeta_fecha, nombre)

        return {
            "carpeta_cliente": carpeta_cliente,
            "carpeta_tipo": carpeta_tipo,
            "carpeta_fecha": carpeta_fecha,
            "ruta_completa": ruta_completa,
        }

    def ejecutar_accion(self, accion: str, archivo_origen: str, destino: dict, carpeta_pendientes: str):
        """
        Mueve el archivo desde origen a la ruta_completa indicada en destino.
        """
        from shutil import move

        ruta_destino = destino["ruta_completa"]
        os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
        move(archivo_origen, ruta_destino)
        return True
EOF
  else
    echo "  services/decision_engine.py ya existe, no se modifica."
  fi
}

patch_run_py_endpoints() {
  echo
  echo "==> [FASE 2] Añadiendo endpoints de Auto-Procesador a run.py (si no existen)..."
  local run_py="${PROJECT_ROOT}/run.py"

  if [[ ! -f "${run_py}" ]]; then
    echo "  [AVISO] No se encontró run.py, creando esqueleto mínimo Flask y añadiendo endpoints."
    cat > "${run_py}" <<'EOF'
import os
import shutil
from flask import Flask, jsonify, request, send_file

app = Flask(__name__)

BASE_DIR = os.path.expanduser('~/Desktop/EXPEDIENTES_LEXDOCS')

@app.route("/")
def index():
    return "LexDocs backend en ejecución"

if __name__ == '__main__':
    app.run(debug=True)
EOF
  fi

  # Backup antes de modificar
  backup_file "${run_py}"

  # Comprobar si ya están los endpoints
  if grep -q "AUTO-PROCESADOR - API ENDPOINTS" "${run_py}"; then
    echo "  Endpoints de auto-procesador ya existen en run.py, no se tocan."
    return 0
  fi

  # Insertar endpoints antes del bloque if __name__ == '__main__':
  echo "  Inyectando endpoints de auto-procesador en run.py..."
  tmpfile="$(mktemp)"

  python <<'PYEOF' "${run_py}" "${tmpfile}"
import sys, io

run_path = sys.argv[1]
out_path = sys.argv[2]

with open(run_path, "r", encoding="utf-8") as f:
    content = f.read()

marker = "if __name__ == '__main__':"
if marker not in content:
    # Si no existe el marker, simplemente añadimos al final
    new_content = content + "\n\n" + """# ============================================
# AUTO-PROCESADOR - API ENDPOINTS
# ============================================

from services.db_service import DatabaseService
from services.decision_engine import DecisionEngine

db_service = DatabaseService()
decision_engine = DecisionEngine()

@app.route('/api/autoprocesador/stats')
def autoprocesador_stats():
    try:
        stats = db_service.obtener_estadisticas_hoy()
        total = stats['total_hoy']
        if total > 0:
            stats['porcentaje_auto'] = round((stats['automaticos'] / total) * 100, 1)
            stats['porcentaje_revision'] = round((stats['en_revision'] / total) * 100, 1)
            stats['porcentaje_errores'] = round((stats['errores'] / total) * 100, 1)
        else:
            stats['porcentaje_auto'] = 0
            stats['porcentaje_revision'] = 0
            stats['porcentaje_errores'] = 0
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/cola-revision')
def autoprocesador_cola_revision():
    try:
        documentos = db_service.obtener_cola_revision()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/procesados-hoy')
def autoprocesador_procesados_hoy():
    try:
        documentos = db_service.obtener_procesados_hoy()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/documento/<int:doc_id>')
def autoprocesador_documento(doc_id):
    try:
        documento = db_service.obtener_documento(doc_id)
        if documento:
            return jsonify({'success': True, 'documento': documento})
        else:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/aprobar/<int:doc_id>', methods=['POST'])
def autoprocesador_aprobar(doc_id):
    try:
        data = request.json
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404

        usuario_modifico = data.get('usuario_modifico', False)

        if usuario_modifico:
            updates = {}
            for key in ('cliente_codigo', 'cliente_detectado', 'tipo_documento', 'carpeta_sugerida'):
                if data.get(key):
                    updates[key] = data[key]
            if updates:
                db_service.actualizar_documento(doc_id, updates)
                documento = db_service.obtener_documento(doc_id)

        analisis = {
            'cliente_codigo': documento.get('cliente_codigo'),
            'tipo_documento': documento.get('tipo_documento'),
            'fecha_documento': documento.get('fecha_documento'),
            'archivo_original': documento.get('archivo_original'),
        }

        destino = decision_engine.construir_ruta_destino(analisis, BASE_DIR)

        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )

        if not os.path.exists(archivo_origen):
            return jsonify({'success': False, 'error': 'Archivo original no encontrado'}), 404

        exito = decision_engine.ejecutar_accion(
            'auto_process',
            archivo_origen,
            destino,
            os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS')
        )

        if exito:
            db_service.aprobar_documento(doc_id, destino['ruta_completa'], usuario_modifico)
            db_service.registrar_log('info', 'dashboard',
                                     f"Usuario aprobó documento: {documento.get('archivo_original')}", doc_id)
            return jsonify({
                'success': True,
                'mensaje': 'Documento aprobado y guardado',
                'ruta_destino': destino['ruta_completa']
            })
        else:
            return jsonify({'success': False, 'error': 'Error al guardar archivo'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/rechazar/<int:doc_id>', methods=['POST'])
def autoprocesador_rechazar(doc_id):
    try:
        data = request.json or {}
        motivo = data.get('motivo', 'Rechazado por usuario')

        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404

        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )

        if os.path.exists(archivo_origen):
            manual_dir = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                'REVISAR_MANUAL'
            )
            os.makedirs(manual_dir, exist_ok=True)
            shutil.move(archivo_origen, os.path.join(manual_dir, documento.get('archivo_original', '')))

        db_service.rechazar_documento(doc_id, motivo)
        db_service.registrar_log('warning', 'dashboard',
                                 f"Usuario rechazó documento: {documento.get('archivo_original')}", doc_id)

        return jsonify({'success': True, 'mensaje': 'Documento rechazado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/clientes')
def autoprocesador_clientes():
    try:
        clientes = []
        if os.path.isdir(BASE_DIR):
            for item in os.listdir(BASE_DIR):
                item_path = os.path.join(BASE_DIR, item)
                if os.path.isdir(item_path) and not item.startswith('.') and not item.startswith('_'):
                    partes = item.split('_', 2)
                    if len(partes) >= 3:
                        nombre = partes[2].replace('_', ' ')
                    else:
                        nombre = item
                    clientes.append({'codigo': item, 'nombre': nombre})
        clientes.sort(key=lambda x: x['codigo'])
        return jsonify({'success': True, 'clientes': clientes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/pdf/<int:doc_id>')
def autoprocesador_pdf(doc_id):
    try:
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return "Documento no encontrado", 404

        archivo = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo):
            archivo = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )

        if not os.path.exists(archivo):
            return "Archivo no encontrado", 404

        return send_file(archivo, mimetype='application/pdf')
    except Exception as e:
        return str(e), 500
"""
else:
    parts = content.split(marker)
    new_content = parts[0].rstrip() + "\n\n" + """# ============================================
# AUTO-PROCESADOR - API ENDPOINTS
# ============================================

from services.db_service import DatabaseService
from services.decision_engine import DecisionEngine

db_service = DatabaseService()
decision_engine = DecisionEngine()

@app.route('/api/autoprocesador/stats')
def autoprocesador_stats():
    try:
        stats = db_service.obtener_estadisticas_hoy()
        total = stats['total_hoy']
        if total > 0:
            stats['porcentaje_auto'] = round((stats['automaticos'] / total) * 100, 1)
            stats['porcentaje_revision'] = round((stats['en_revision'] / total) * 100, 1)
            stats['porcentaje_errores'] = round((stats['errores'] / total) * 100, 1)
        else:
            stats['porcentaje_auto'] = 0
            stats['porcentaje_revision'] = 0
            stats['porcentaje_errores'] = 0
        return jsonify({'success': True, 'stats': stats})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/cola-revision')
def autoprocesador_cola_revision():
    try:
        documentos = db_service.obtener_cola_revision()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/procesados-hoy')
def autoprocesador_procesados_hoy():
    try:
        documentos = db_service.obtener_procesados_hoy()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/documento/<int:doc_id>')
def autoprocesador_documento(doc_id):
    try:
        documento = db_service.obtener_documento(doc_id)
        if documento:
            return jsonify({'success': True, 'documento': documento})
        else:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/aprobar/<int:doc_id>', methods=['POST'])
def autoprocesador_aprobar(doc_id):
    try:
        data = request.json
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404

        usuario_modifico = data.get('usuario_modifico', False)

        if usuario_modifico:
            updates = {}
            for key in ('cliente_codigo', 'cliente_detectado', 'tipo_documento', 'carpeta_sugerida'):
                if data.get(key):
                    updates[key] = data[key]
            if updates:
                db_service.actualizar_documento(doc_id, updates)
                documento = db_service.obtener_documento(doc_id)

        analisis = {
            'cliente_codigo': documento.get('cliente_codigo'),
            'tipo_documento': documento.get('tipo_documento'),
            'fecha_documento': documento.get('fecha_documento'),
            'archivo_original': documento.get('archivo_original'),
        }

        destino = decision_engine.construir_ruta_destino(analisis, BASE_DIR)

        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )

        if not os.path.exists(archivo_origen):
            return jsonify({'success': False, 'error': 'Archivo original no encontrado'}), 404

        exito = decision_engine.ejecutar_accion(
            'auto_process',
            archivo_origen,
            destino,
            os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS')
        )

        if exito:
            db_service.aprobar_documento(doc_id, destino['ruta_completa'], usuario_modifico)
            db_service.registrar_log('info', 'dashboard',
                                     f"Usuario aprobó documento: {documento.get('archivo_original')}", doc_id)
            return jsonify({
                'success': True,
                'mensaje': 'Documento aprobado y guardado',
                'ruta_destino': destino['ruta_completa']
            })
        else:
            return jsonify({'success': False, 'error': 'Error al guardar archivo'})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/rechazar/<int:doc_id>', methods=['POST'])
def autoprocesador_rechazar(doc_id):
    try:
        data = request.json or {}
        motivo = data.get('motivo', 'Rechazado por usuario')

        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404

        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )

        if os.path.exists(archivo_origen):
            manual_dir = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                'REVISAR_MANUAL'
            )
            os.makedirs(manual_dir, exist_ok=True)
            shutil.move(archivo_origen, os.path.join(manual_dir, documento.get('archivo_original', '')))

        db_service.rechazar_documento(doc_id, motivo)
        db_service.registrar_log('warning', 'dashboard',
                                 f"Usuario rechazó documento: {documento.get('archivo_original')}", doc_id)

        return jsonify({'success': True, 'mensaje': 'Documento rechazado'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/clientes')
def autoprocesador_clientes():
    try:
        clientes = []
        if os.path.isdir(BASE_DIR):
            for item in os.listdir(BASE_DIR):
                item_path = os.path.join(BASE_DIR, item)
                if os.path.isdir(item_path) and not item.startswith('.') and not item.startswith('_'):
                    partes = item.split('_', 2)
                    if len(partes) >= 3:
                        nombre = partes[2].replace('_', ' ')
                    else:
                        nombre = item
                    clientes.append({'codigo': item, 'nombre': nombre})
        clientes.sort(key=lambda x: x['codigo'])
        return jsonify({'success': True, 'clientes': clientes})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/pdf/<int:doc_id>')
def autoprocesador_pdf(doc_id):
    try:
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return "Documento no encontrado", 404

        archivo = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo):
            archivo = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )

        if not os.path.exists(archivo):
            return "Archivo no encontrado", 404

        return send_file(archivo, mimetype='application/pdf')
    except Exception as e:
        return str(e), 500
"""
    + "\n\n" + marker + content.split(marker, 1)[1]

with open(out_path, "w", encoding="utf-8") as f:
    f.write(new_content)
PYEOF

  mv "${tmpfile}" "${run_py}"
}

main() {
  echo "==> Iniciando setup completo (Fase 1 + Fase 2)..."
  ensure_python_venv
  ensure_python_services
  patch_run_py_endpoints
  ensure_react_frontend
  echo
  echo "==============================================="
  echo "  SETUP COMPLETADO SIN ERRORES"
  echo "==============================================="
  echo "Backups en: ${BACKUP_DIR}"
  echo
  echo "Para arrancar backend:"
  echo "  cd \"${PROJECT_ROOT}\""
  echo "  source .venv/bin/activate"
  echo "  python run.py"
  echo
  echo "Para arrancar frontend (si usas la carpeta frontend):"
  echo "  cd \"${PROJECT_ROOT}/frontend\""
  echo "  npm run dev   # o el comando que uses en tu package.json"
}

main "$@"
