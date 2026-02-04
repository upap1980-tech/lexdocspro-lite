#!/usr/bin/env bash
#
# setup_lexdocs_ajustado.sh - Configuración automática Fase 1 y Fase 2
# Adaptado para: upap1980-tech/lexdocspro-lite
# Estructura detectada: Flask backend + templates/static (sin carpeta frontend React separada)

set -euo pipefail

# ============= CONFIGURACIÓN =============
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/_backups_$(date +%Y%m%d_%H%M%S)"
PYTHON_BIN="${PYTHON_BIN:-python3}"
VENV_DIR="${PROJECT_ROOT}/.venv"

# Colores para output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=================================================${NC}"
echo -e "${BLUE}  LEXDOCS PRO LITE - SETUP AUTOMÁTICO${NC}"
echo -e "${BLUE}  Fase 1: Backend Services + DB${NC}"
echo -e "${BLUE}  Fase 2: API Endpoints + Dashboard${NC}"
echo -e "${BLUE}=================================================${NC}"
echo -e "Proyecto:      ${GREEN}${PROJECT_ROOT}${NC}"
echo -e "Backup dir:    ${YELLOW}${BACKUP_DIR}${NC}"
echo

mkdir -p "${BACKUP_DIR}"

# ============= FUNCIONES AUXILIARES =============

log_info() {
    echo -e "${GREEN}✓${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}⚠${NC} $1"
}

log_error() {
    echo -e "${RED}✗${NC} $1"
}

log_step() {
    echo
    echo -e "${BLUE}==> $1${NC}"
}

backup_file() {
    local file="$1"
    if [[ -f "${file}" ]]; then
        local rel
        rel=$(realpath --relative-to="${PROJECT_ROOT}" "${file}" 2>/dev/null || basename "${file}")
        local dest="${BACKUP_DIR}/${rel}"
        mkdir -p "$(dirname "${dest}")"
        cp -p "${file}" "${dest}"
        log_info "Backup: ${rel}"
    fi
}

# ============= FASE 0: VALIDACIÓN =============

validate_environment() {
    log_step "FASE 0: Validando entorno..."
    
    # Verificar Python
    if ! command -v "${PYTHON_BIN}" &> /dev/null; then
        log_error "Python3 no encontrado. Instala Python 3.8+ primero."
        exit 1
    fi
    log_info "Python encontrado: $(${PYTHON_BIN} --version)"
    
    # Verificar estructura del proyecto
    if [[ ! -f "${PROJECT_ROOT}/run.py" ]]; then
        log_error "run.py no encontrado. ¿Estás en el directorio correcto?"
        exit 1
    fi
    log_info "Estructura del proyecto verificada"
    
    # Verificar carpetas existentes
    [[ -d "${PROJECT_ROOT}/services" ]] && log_info "Carpeta services/ existe"
    [[ -d "${PROJECT_ROOT}/templates" ]] && log_info "Carpeta templates/ existe"
    [[ -d "${PROJECT_ROOT}/static" ]] && log_info "Carpeta static/ existe"
}

# ============= FASE 1: SERVICIOS BACKEND =============

setup_python_environment() {
    log_step "FASE 1.1: Configurando entorno Python..."
    
    if [[ -d "${VENV_DIR}" ]]; then
        log_warn "venv existente encontrado, reutilizando..."
    else
        log_info "Creando nuevo venv en ${VENV_DIR}..."
        "${PYTHON_BIN}" -m venv "${VENV_DIR}"
    fi
    
    # Activar venv
    # shellcheck disable=SC1091
    source "${VENV_DIR}/bin/activate"
    
    # Actualizar pip
    pip install --upgrade pip --quiet
    
    # Instalar dependencias
    if [[ -f "${PROJECT_ROOT}/requirements.txt" ]]; then
        log_info "Instalando dependencias desde requirements.txt..."
        pip install -r "${PROJECT_ROOT}/requirements.txt" --quiet
    else
        log_warn "requirements.txt no encontrado"
    fi
}

create_db_service() {
    log_step "FASE 1.2: Verificando DatabaseService..."
    
    local db_service="${PROJECT_ROOT}/services/db_service.py"
    
    if [[ -f "${db_service}" ]]; then
        log_warn "db_service.py ya existe, NO se modificará"
        return 0
    fi
    
    log_info "Creando services/db_service.py..."
    mkdir -p "${PROJECT_ROOT}/services"
    
    cat > "${db_service}" <<'PYEOF'
"""
DatabaseService - Gestión de base de datos para LexDocs Auto-Procesador
"""
import os
import sqlite3
from datetime import datetime
from typing import Optional, Dict, List

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "lexdocs_autoprocesador.db")

class DatabaseService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Inicializar esquema de base de datos"""
        conn = self._get_conn()
        cur = conn.cursor()
        
        # Tabla de documentos procesados
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo_original TEXT NOT NULL,
            ruta_temporal TEXT,
            cliente_codigo TEXT,
            cliente_detectado TEXT,
            tipo_documento TEXT,
            fecha_documento TEXT,
            carpeta_sugerida TEXT,
            estado TEXT DEFAULT 'pendiente',
            confianza REAL DEFAULT 0.0,
            requiere_revision BOOLEAN DEFAULT 0,
            ruta_definitiva TEXT,
            usuario_modifico BOOLEAN DEFAULT 0,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            procesado_en TIMESTAMP,
            metadata TEXT
        );
        """)
        
        # Tabla de logs
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nivel TEXT NOT NULL,
            origen TEXT NOT NULL,
            mensaje TEXT NOT NULL,
            documento_id INTEGER,
            creado_en TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (documento_id) REFERENCES documentos(id)
        );
        """)
        
        # Índices para mejorar rendimiento
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documentos_estado ON documentos(estado)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_documentos_fecha ON documentos(creado_en)")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_logs_nivel ON logs(nivel)")
        
        conn.commit()
        conn.close()

    def registrar_log(self, nivel: str, origen: str, mensaje: str, documento_id: Optional[int] = None):
        """Registrar entrada en log"""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (nivel, origen, mensaje, documento_id) VALUES (?, ?, ?, ?)",
            (nivel, origen, mensaje, documento_id),
        )
        conn.commit()
        conn.close()

    def obtener_estadisticas_hoy(self) -> Dict:
        """Obtener estadísticas de documentos procesados hoy"""
        conn = self._get_conn()
        cur = conn.cursor()
        hoy = datetime.now().date().isoformat()
        
        cur.execute("SELECT COUNT(*) as total FROM documentos WHERE date(creado_en) = ?", (hoy,))
        total = cur.fetchone()['total']
        
        cur.execute("SELECT COUNT(*) as automaticos FROM documentos WHERE estado = 'auto'")
        automaticos = cur.fetchone()['automaticos']
        
        cur.execute("SELECT COUNT(*) as revision FROM documentos WHERE estado = 'revision'")
        en_revision = cur.fetchone()['revision']
        
        cur.execute("SELECT COUNT(*) as errores FROM documentos WHERE estado = 'error'")
        errores = cur.fetchone()['errores']
        
        conn.close()
        
        return {
            "total_hoy": total,
            "automaticos": automaticos,
            "en_revision": en_revision,
            "errores": errores,
        }

    def obtener_cola_revision(self) -> List[Dict]:
        """Obtener documentos que requieren revisión manual"""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            SELECT * FROM documentos 
            WHERE estado = 'revision' 
            ORDER BY creado_en DESC
        """)
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows

    def obtener_procesados_hoy(self) -> List[Dict]:
        """Obtener todos los documentos procesados hoy"""
        conn = self._get_conn()
        cur = conn.cursor()
        hoy = datetime.now().date().isoformat()
        cur.execute("""
            SELECT * FROM documentos 
            WHERE date(creado_en) = ?
            ORDER BY creado_en DESC
        """, (hoy,))
        rows = [dict(row) for row in cur.fetchall()]
        conn.close()
        return rows

    def obtener_documento(self, doc_id: int) -> Optional[Dict]:
        """Obtener documento por ID"""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM documentos WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def actualizar_documento(self, doc_id: int, updates: Dict):
        """Actualizar campos de documento"""
        if not updates:
            return
        
        conn = self._get_conn()
        cur = conn.cursor()
        sets = ", ".join([f"{k} = ?" for k in updates.keys()])
        values = list(updates.values()) + [doc_id]
        cur.execute(f"UPDATE documentos SET {sets} WHERE id = ?", values)
        conn.commit()
        conn.close()

    def aprobar_documento(self, doc_id: int, ruta_definitiva: str, usuario_modifico: bool):
        """Marcar documento como aprobado"""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE documentos 
            SET estado = 'auto', 
                ruta_definitiva = ?,
                usuario_modifico = ?,
                procesado_en = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (ruta_definitiva, 1 if usuario_modifico else 0, doc_id))
        conn.commit()
        conn.close()

    def rechazar_documento(self, doc_id: int, motivo: str):
        """Marcar documento como rechazado"""
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
            UPDATE documentos 
            SET estado = 'rechazado',
                metadata = ?,
                procesado_en = CURRENT_TIMESTAMP
            WHERE id = ?
        """, (motivo, doc_id))
        conn.commit()
        conn.close()
PYEOF

    log_info "db_service.py creado correctamente"
}

create_decision_engine() {
    log_step "FASE 1.3: Verificando DecisionEngine..."
    
    local decision_engine="${PROJECT_ROOT}/services/decision_engine.py"
    
    if [[ -f "${decision_engine}" ]]; then
        log_warn "decision_engine.py ya existe, NO se modificará"
        return 0
    fi
    
    log_info "Creando services/decision_engine.py..."
    
    cat > "${decision_engine}" <<'PYEOF'
"""
DecisionEngine - Motor de decisiones para auto-procesamiento de documentos
"""
import os
import shutil
from datetime import datetime
from typing import Dict, Optional

class DecisionEngine:
    def __init__(self):
        self.tipos_permitidos = ['Contrato', 'Factura', 'Escritura', 'Sentencia', 'Demanda', 'Otros']

    def construir_ruta_destino(self, analisis: Dict, base_dir: str) -> Dict:
        """
        Construye la ruta de destino según el análisis del documento
        
        Estructura: BASE_DIR/CLIENTE_CODIGO/TIPO_DOC/AAAA_MM/archivo.pdf
        """
        cliente = analisis.get("cliente_codigo") or "SIN_CLIENTE"
        tipo = analisis.get("tipo_documento") or "Otros"
        fecha_str = analisis.get("fecha_documento") or datetime.now().strftime("%Y%m%d")
        nombre = analisis.get("archivo_original") or "documento.pdf"

        # Extraer año y mes
        if len(fecha_str) >= 8:  # formato YYYYMMDD
            ano = fecha_str[:4]
            mes = fecha_str[4:6]
        else:
            ano = datetime.now().strftime("%Y")
            mes = datetime.now().strftime("%m")

        # Construir ruta
        carpeta_cliente = os.path.join(base_dir, cliente)
        carpeta_tipo = os.path.join(carpeta_cliente, tipo)
        carpeta_fecha = os.path.join(carpeta_tipo, f"{ano}_{mes}")
        
        # Crear directorios si no existen
        os.makedirs(carpeta_fecha, exist_ok=True)

        ruta_completa = os.path.join(carpeta_fecha, nombre)
        
        # Si el archivo ya existe, añadir sufijo
        if os.path.exists(ruta_completa):
            base, ext = os.path.splitext(nombre)
            contador = 1
            while os.path.exists(ruta_completa):
                nuevo_nombre = f"{base}_{contador}{ext}"
                ruta_completa = os.path.join(carpeta_fecha, nuevo_nombre)
                contador += 1

        return {
            "carpeta_cliente": carpeta_cliente,
            "carpeta_tipo": carpeta_tipo,
            "carpeta_fecha": carpeta_fecha,
            "ruta_completa": ruta_completa,
            "nombre_final": os.path.basename(ruta_completa)
        }

    def ejecutar_accion(self, accion: str, archivo_origen: str, destino: Dict, carpeta_pendientes: str) -> bool:
        """
        Ejecuta la acción de movimiento del archivo
        
        Args:
            accion: Tipo de acción ('auto_process', 'manual_review', etc)
            archivo_origen: Ruta completa del archivo a mover
            destino: Dict con info de destino (de construir_ruta_destino)
            carpeta_pendientes: Carpeta de documentos pendientes
            
        Returns:
            bool: True si tuvo éxito, False en caso contrario
        """
        try:
            if not os.path.exists(archivo_origen):
                print(f"❌ Archivo origen no existe: {archivo_origen}")
                return False
            
            ruta_destino = destino["ruta_completa"]
            
            # Crear directorio destino si no existe
            os.makedirs(os.path.dirname(ruta_destino), exist_ok=True)
            
            # Mover archivo
            shutil.move(archivo_origen, ruta_destino)
            
            print(f"✓ Archivo movido: {os.path.basename(archivo_origen)} → {ruta_destino}")
            return True
            
        except Exception as e:
            print(f"❌ Error al mover archivo: {str(e)}")
            return False

    def validar_confianza(self, confianza: float, umbral: float = 0.85) -> bool:
        """Determina si la confianza es suficiente para procesamiento automático"""
        return confianza >= umbral
PYEOF

    log_info "decision_engine.py creado correctamente"
}

# ============= FASE 2: API ENDPOINTS =============

patch_run_py() {
    log_step "FASE 2.1: Añadiendo endpoints API a run.py..."
    
    local run_py="${PROJECT_ROOT}/run.py"
    
    if [[ ! -f "${run_py}" ]]; then
        log_error "run.py no encontrado"
        return 1
    fi
    
    # Verificar si ya existen los endpoints
    if grep -q "AUTO-PROCESADOR - API ENDPOINTS" "${run_py}"; then
        log_warn "Los endpoints ya existen en run.py, omitiendo..."
        return 0
    fi
    
    # Backup antes de modificar
    backup_file "${run_py}"
    
    log_info "Inyectando endpoints en run.py..."
    
    # Crear archivo temporal con los endpoints
    local endpoints_file="${PROJECT_ROOT}/_endpoints_temp.py"
    
    cat > "${endpoints_file}" <<'ENDPOINTSEOF'

# ============================================
# AUTO-PROCESADOR - API ENDPOINTS
# ============================================

from services.db_service import DatabaseService
from services.decision_engine import DecisionEngine

# Inicializar servicios
db_service = DatabaseService()
decision_engine = DecisionEngine()

@app.route('/api/autoprocesador/stats')
def autoprocesador_stats():
    """Obtener estadísticas del auto-procesador"""
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
    """Obtener documentos que requieren revisión"""
    try:
        documentos = db_service.obtener_cola_revision()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/procesados-hoy')
def autoprocesador_procesados_hoy():
    """Obtener documentos procesados hoy"""
    try:
        documentos = db_service.obtener_procesados_hoy()
        return jsonify({'success': True, 'documentos': documentos, 'total': len(documentos)})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/documento/<int:doc_id>')
def autoprocesador_documento(doc_id):
    """Obtener detalles de documento"""
    try:
        documento = db_service.obtener_documento(doc_id)
        if documento:
            return jsonify({'success': True, 'documento': documento})
        return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/aprobar/<int:doc_id>', methods=['POST'])
def autoprocesador_aprobar(doc_id):
    """Aprobar documento y guardarlo"""
    try:
        data = request.json or {}
        documento = db_service.obtener_documento(doc_id)
        
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Verificar si usuario modificó datos
        usuario_modifico = data.get('usuario_modifico', False)
        
        if usuario_modifico:
            updates = {}
            for key in ['cliente_codigo', 'cliente_detectado', 'tipo_documento', 'carpeta_sugerida']:
                if data.get(key):
                    updates[key] = data[key]
            if updates:
                db_service.actualizar_documento(doc_id, updates)
                documento = db_service.obtener_documento(doc_id)
        
        # Construir ruta destino
        analisis = {
            'cliente_codigo': documento.get('cliente_codigo'),
            'tipo_documento': documento.get('tipo_documento'),
            'fecha_documento': documento.get('fecha_documento'),
            'archivo_original': documento.get('archivo_original'),
        }
        
        base_dir = os.path.expanduser('~/Desktop/EXPEDIENTES_LEXDOCS')
        destino = decision_engine.construir_ruta_destino(analisis, base_dir)
        
        # Buscar archivo origen
        archivo_origen = documento.get('ruta_temporal') or ''
        if not os.path.exists(archivo_origen):
            archivo_origen = os.path.join(
                os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS'),
                documento.get('archivo_original', '')
            )
        
        if not os.path.exists(archivo_origen):
            return jsonify({'success': False, 'error': 'Archivo no encontrado'}), 404
        
        # Ejecutar acción
        exito = decision_engine.ejecutar_accion(
            'auto_process',
            archivo_origen,
            destino,
            os.path.expanduser('~/Desktop/PENDIENTES_LEXDOCS')
        )
        
        if exito:
            db_service.aprobar_documento(doc_id, destino['ruta_completa'], usuario_modifico)
            db_service.registrar_log('info', 'dashboard', 
                                   f"Usuario aprobó: {documento.get('archivo_original')}", doc_id)
            return jsonify({
                'success': True,
                'mensaje': 'Documento aprobado y guardado',
                'ruta_destino': destino['ruta_completa']
            })
        
        return jsonify({'success': False, 'error': 'Error al guardar archivo'})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/rechazar/<int:doc_id>', methods=['POST'])
def autoprocesador_rechazar(doc_id):
    """Rechazar documento"""
    try:
        data = request.json or {}
        motivo = data.get('motivo', 'Rechazado por usuario')
        
        documento = db_service.obtener_documento(doc_id)
        if not documento:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Mover a REVISAR_MANUAL
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
                               f"Usuario rechazó: {documento.get('archivo_original')}", doc_id)
        
        return jsonify({'success': True, 'mensaje': 'Documento rechazado'})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/clientes')
def autoprocesador_clientes():
    """Listar clientes existentes"""
    try:
        base_dir = os.path.expanduser('~/Desktop/EXPEDIENTES_LEXDOCS')
        clientes = []
        
        if os.path.isdir(base_dir):
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path) and not item.startswith('.') and not item.startswith('_'):
                    partes = item.split('_', 2)
                    nombre = partes[2].replace('_', ' ') if len(partes) >= 3 else item
                    clientes.append({'codigo': item, 'nombre': nombre})
        
        clientes.sort(key=lambda x: x['codigo'])
        return jsonify({'success': True, 'clientes': clientes})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/autoprocesador/pdf/<int:doc_id>')
def autoprocesador_pdf(doc_id):
    """Servir PDF para vista previa"""
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

ENDPOINTSEOF
    
    # Insertar antes de if __name__ == '__main__':
    python3 <<PYEOF
import sys

run_path = "${run_py}"
endpoints_path = "${endpoints_file}"

with open(run_path, 'r', encoding='utf-8') as f:
    content = f.read()

with open(endpoints_path, 'r', encoding='utf-8') as f:
    endpoints = f.read()

marker = "if __name__ == '__main__':"

if marker in content:
    parts = content.split(marker, 1)
    new_content = parts[0].rstrip() + "\n" + endpoints + "\n\n" + marker + parts[1]
else:
    new_content = content + "\n" + endpoints

with open(run_path, 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Endpoints inyectados correctamente")
PYEOF
    
    # Limpiar archivo temporal
    rm -f "${endpoints_file}"
    
    log_info "run.py actualizado con endpoints de auto-procesador"
}

# ============= VERIFICACIÓN FINAL =============

verify_setup() {
    log_step "Verificando instalación..."
    
    local errors=0
    
    # Verificar archivos clave
    [[ -f "${PROJECT_ROOT}/services/db_service.py" ]] || { log_error "db_service.py no encontrado"; ((errors++)); }
    [[ -f "${PROJECT_ROOT}/services/decision_engine.py" ]] || { log_error "decision_engine.py no encontrado"; ((errors++)); }
    [[ -f "${PROJECT_ROOT}/run.py" ]] || { log_error "run.py no encontrado"; ((errors++)); }
    
    # Verificar que los endpoints estén en run.py
    if grep -q "AUTO-PROCESADOR - API ENDPOINTS" "${PROJECT_ROOT}/run.py"; then
        log_info "Endpoints verificados en run.py"
    else
        log_error "Endpoints NO encontrados en run.py"
        ((errors++))
    fi
    
    # Verificar base de datos se puede inicializar
    if [[ -d "${VENV_DIR}" ]]; then
        source "${VENV_DIR}/bin/activate"
        python3 -c "from services.db_service import DatabaseService; db = DatabaseService(); print('✓ DB inicializada')" 2>/dev/null || {
            log_error "Error al inicializar base de datos"
            ((errors++))
        }
    fi
    
    if [[ ${errors} -eq 0 ]]; then
        log_info "Todas las verificaciones pasadas ✓"
        return 0
    else
        log_error "Se encontraron ${errors} errores"
        return 1
    fi
}

# ============= MAIN =============

main() {
    validate_environment
    setup_python_environment
    create_db_service
    create_decision_engine
    patch_run_py
    verify_setup
    
    echo
    echo -e "${GREEN}=================================================${NC}"
    echo -e "${GREEN}  ✓ SETUP COMPLETADO CON ÉXITO${NC}"
    echo -e "${GREEN}=================================================${NC}"
    echo
    echo -e "📦 Backups guardados en: ${YELLOW}${BACKUP_DIR}${NC}"
    echo
    echo -e "${BLUE}Para iniciar el sistema:${NC}"
    echo -e "  ${GREEN}1.${NC} Activar entorno: ${YELLOW}source .venv/bin/activate${NC}"
    echo -e "  ${GREEN}2.${NC} Iniciar servidor: ${YELLOW}python run.py${NC}"
    echo -e "  ${GREEN}3.${NC} Abrir navegador: ${YELLOW}http://localhost:5000${NC}"
    echo
    echo -e "${BLUE}Nuevos endpoints API disponibles:${NC}"
    echo -e "  • /api/autoprocesador/stats"
    echo -e "  • /api/autoprocesador/cola-revision"
    echo -e "  • /api/autoprocesador/procesados-hoy"
    echo -e "  • /api/autoprocesador/aprobar/<id>"
    echo -e "  • /api/autoprocesador/rechazar/<id>"
    echo
}

main "$@"
