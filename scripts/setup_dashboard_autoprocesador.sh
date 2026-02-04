#!/usr/bin/env bash
#
# setup_dashboard_autoprocesador.sh
# Integra la 4ª pestaña "Auto-Procesador" en LexDocsPro LITE
# SIN sobrescribir código existente - Solo añade modificaciones

set -euo pipefail

# ============= CONFIGURACIÓN =============
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKUP_DIR="${PROJECT_ROOT}/_backups_dashboard_$(date +%Y%m%d_%H%M%S)"

# Colores
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

echo -e "${BLUE}===============================================${NC}"
echo -e "${BLUE}  🎨 INTEGRACIÓN DASHBOARD AUTO-PROCESADOR${NC}"
echo -e "${BLUE}===============================================${NC}"
echo -e "Proyecto:  ${GREEN}${PROJECT_ROOT}${NC}"
echo -e "Backups:   ${YELLOW}${BACKUP_DIR}${NC}"
echo

mkdir -p "${BACKUP_DIR}"

# ============= FUNCIONES =============

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

# ============= PASO 1: ACTUALIZAR index.html =============

update_index_html() {
    log_step "PASO 1: Actualizando templates/index.html"
    
    local index_html="${PROJECT_ROOT}/templates/index.html"
    
    if [[ ! -f "${index_html}" ]]; then
        log_error "index.html no encontrado"
        return 1
    fi
    
    # Backup
    backup_file "${index_html}"
    
    # Verificar si ya existe la pestaña
    if grep -q "tab-autoprocesador" "${index_html}"; then
        log_warn "La pestaña Auto-Procesador ya existe en index.html"
        return 0
    fi
    
    log_info "Añadiendo 4ª pestaña al HTML..."
    
    # Crear archivo temporal con el nuevo tab button
    local tab_button='            <button class="tab-btn" onclick="switchTab('\''autoprocesador'\'')">🤖 Auto-Procesador</button>'
    
    # Insertar tab button después de la línea que contiene 'Analizador LexNET'
    sed -i.tmp '/Analizador LexNET/a\
'"${tab_button}" "${index_html}"
    
    # Crear archivo con el contenido del nuevo tab
    cat > "${PROJECT_ROOT}/_tab_autoprocesador.html" <<'TABEOF'

        <!-- TAB 4: AUTO-PROCESADOR -->
        <div id="tab-autoprocesador" class="tab-content">
            <div class="autoprocesador-layout">
                <!-- Panel Izquierdo: Dashboard con estadísticas -->
                <div class="panel autoprocesador-stats">
                    <h2>📊 Dashboard Auto-Procesador</h2>
                    
                    <div class="stats-cards">
                        <div class="stat-card stat-total">
                            <div class="stat-icon">📁</div>
                            <div class="stat-info">
                                <div class="stat-value" id="stat-total">0</div>
                                <div class="stat-label">Total Hoy</div>
                            </div>
                        </div>
                        
                        <div class="stat-card stat-auto">
                            <div class="stat-icon">✅</div>
                            <div class="stat-info">
                                <div class="stat-value" id="stat-auto">0</div>
                                <div class="stat-label">Automáticos</div>
                                <div class="stat-percent" id="percent-auto">0%</div>
                            </div>
                        </div>
                        
                        <div class="stat-card stat-revision">
                            <div class="stat-icon">⚠️</div>
                            <div class="stat-info">
                                <div class="stat-value" id="stat-revision">0</div>
                                <div class="stat-label">En Revisión</div>
                                <div class="stat-percent" id="percent-revision">0%</div>
                            </div>
                        </div>
                        
                        <div class="stat-card stat-error">
                            <div class="stat-icon">❌</div>
                            <div class="stat-info">
                                <div class="stat-value" id="stat-error">0</div>
                                <div class="stat-label">Errores</div>
                                <div class="stat-percent" id="percent-error">0%</div>
                            </div>
                        </div>
                    </div>
                    
                    <div class="stats-actions">
                        <button onclick="refreshAutoProcesadorStats()" class="btn-refresh">🔄 Actualizar</button>
                        <button onclick="showAllProcessed()" class="btn-secondary">📋 Ver Todos</button>
                    </div>
                    
                    <h3 style="margin-top: 20px;">⏳ Cola de Revisión</h3>
                    <div id="documentsList" class="documents-list">
                        <p class="placeholder">Cargando documentos...</p>
                    </div>
                </div>
                
                <!-- Panel Central: Visor de Documento -->
                <div class="panel autoprocesador-viewer">
                    <h2>👁️ Vista Previa</h2>
                    <div id="autoProcesadorPdfViewer" class="pdf-container">
                        <p class="placeholder">Selecciona un documento de la lista para ver detalles</p>
                    </div>
                </div>
                
                <!-- Panel Derecho: Detalles y Acciones -->
                <div class="panel autoprocesador-actions">
                    <h2>📝 Detalles del Documento</h2>
                    
                    <div id="documentDetails" class="document-details hidden">
                        <div class="detail-group">
                            <label>📄 Archivo:</label>
                            <input type="text" id="detail-filename" readonly class="detail-input">
                        </div>
                        
                        <div class="detail-group">
                            <label>👤 Cliente:</label>
                            <input type="text" id="detail-cliente" class="detail-input editable">
                            <select id="detail-cliente-select" class="detail-select">
                                <option value="">-- Seleccionar cliente --</option>
                            </select>
                        </div>
                        
                        <div class="detail-group">
                            <label>📋 Tipo Documento:</label>
                            <select id="detail-tipo" class="detail-select editable">
                                <option value="Contrato">Contrato</option>
                                <option value="Factura">Factura</option>
                                <option value="Escritura">Escritura</option>
                                <option value="Sentencia">Sentencia</option>
                                <option value="Demanda">Demanda</option>
                                <option value="Otros">Otros</option>
                            </select>
                        </div>
                        
                        <div class="detail-group">
                            <label>📅 Fecha Documento:</label>
                            <input type="text" id="detail-fecha" readonly class="detail-input">
                        </div>
                        
                        <div class="detail-group">
                            <label>📁 Carpeta Sugerida:</label>
                            <input type="text" id="detail-carpeta" readonly class="detail-input">
                        </div>
                        
                        <div class="detail-group">
                            <label>🎯 Confianza:</label>
                            <div class="confidence-bar">
                                <div id="detail-confianza-bar" class="confidence-fill" style="width: 0%"></div>
                                <span id="detail-confianza-text" class="confidence-text">0%</span>
                            </div>
                        </div>
                        
                        <div class="alert-info" style="margin: 15px 0;">
                            <strong>💡 Nota:</strong> Puedes modificar el cliente y tipo antes de aprobar.
                        </div>
                        
                        <div class="action-buttons">
                            <button onclick="aprobarDocumento()" class="btn-approve">
                                ✅ Aprobar y Guardar
                            </button>
                            <button onclick="rechazarDocumento()" class="btn-reject">
                                ❌ Rechazar
                            </button>
                        </div>
                    </div>
                    
                    <div id="noDocumentSelected" class="no-selection">
                        <div class="no-selection-icon">📄</div>
                        <p>Selecciona un documento de la lista para ver sus detalles y tomar acción</p>
                    </div>
                </div>
            </div>
        </div>
TABEOF
    
    # Insertar el nuevo tab antes del </div> final del tab-lexnet
    python3 <<PYEOF
with open("${index_html}", 'r', encoding='utf-8') as f:
    content = f.read()

with open("${PROJECT_ROOT}/_tab_autoprocesador.html", 'r', encoding='utf-8') as f:
    new_tab = f.read()

# Buscar el cierre del tab-lexnet
marker = '</div>\n\n        <footer>'
if marker in content:
    parts = content.split(marker, 1)
    new_content = parts[0] + new_tab + '\n\n        <footer>' + parts[1]
else:
    # Intentar con otro marker
    marker2 = '<footer>'
    if marker2 in content:
        parts = content.split(marker2, 1)
        new_content = parts[0] + new_tab + '\n\n        <footer>' + parts[1]
    else:
        print("ERROR: No se encontró el marcador para insertar el nuevo tab")
        exit(1)

with open("${index_html}", 'w', encoding='utf-8') as f:
    f.write(new_content)

print("✓ Tab insertado correctamente")
PYEOF
    
    # Limpiar archivos temporales
    rm -f "${index_html}.tmp"
    rm -f "${PROJECT_ROOT}/_tab_autoprocesador.html"
    
    log_info "index.html actualizado correctamente"
}

# ============= PASO 2: ACTUALIZAR style.css =============

update_style_css() {
    log_step "PASO 2: Actualizando static/css/style.css"
    
    local style_css="${PROJECT_ROOT}/static/css/style.css"
    
    if [[ ! -f "${style_css}" ]]; then
        log_error "style.css no encontrado"
        return 1
    fi
    
    # Backup
    backup_file "${style_css}"
    
    # Verificar si ya existen los estilos
    if grep -q "AUTO-PROCESADOR STYLES" "${style_css}"; then
        log_warn "Los estilos de Auto-Procesador ya existen en style.css"
        return 0
    fi
    
    log_info "Añadiendo estilos CSS..."
    
    # Añadir estilos al final del archivo
    cat >> "${style_css}" <<'CSSEOF'

/* ============================================
   AUTO-PROCESADOR STYLES
   ============================================ */

.autoprocesador-layout {
    display: grid;
    grid-template-columns: 350px 1fr 400px;
    gap: 15px;
    height: calc(100vh - 200px);
}

/* Stats Panel */
.autoprocesador-stats {
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.stats-cards {
    display: grid;
    grid-template-columns: 1fr;
    gap: 12px;
    margin-bottom: 15px;
}

.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    padding: 15px;
    display: flex;
    align-items: center;
    gap: 12px;
    color: white;
    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}

.stat-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 6px 12px rgba(0,0,0,0.15);
}

.stat-card.stat-total {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-card.stat-auto {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
}

.stat-card.stat-revision {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-card.stat-error {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
}

.stat-icon {
    font-size: 2.5rem;
    opacity: 0.9;
}

.stat-info {
    flex: 1;
}

.stat-value {
    font-size: 2rem;
    font-weight: bold;
    line-height: 1;
}

.stat-label {
    font-size: 0.85rem;
    opacity: 0.9;
    margin-top: 4px;
}

.stat-percent {
    font-size: 0.75rem;
    opacity: 0.8;
    margin-top: 2px;
}

.stats-actions {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.stats-actions button {
    flex: 1;
}

/* Documents List */
.documents-list {
    flex: 1;
    overflow-y: auto;
    background: #f8f9fa;
    border-radius: 8px;
    padding: 10px;
}

.document-item {
    background: white;
    border-radius: 8px;
    padding: 12px;
    margin-bottom: 10px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.2s;
}

.document-item:hover {
    border-color: #667eea;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2);
}

.document-item.selected {
    border-color: #667eea;
    background: #f0f4ff;
}

.document-item-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
}

.document-item-name {
    font-weight: 600;
    color: #2d3748;
    font-size: 0.9rem;
}

.document-item-badge {
    padding: 3px 8px;
    border-radius: 12px;
    font-size: 0.7rem;
    font-weight: 600;
}

.badge-revision {
    background: #fff3cd;
    color: #856404;
}

.badge-auto {
    background: #d4edda;
    color: #155724;
}

.badge-error {
    background: #f8d7da;
    color: #721c24;
}

.document-item-info {
    font-size: 0.8rem;
    color: #718096;
}

.document-item-info div {
    margin: 2px 0;
}

/* Viewer Panel */
.autoprocesador-viewer {
    display: flex;
    flex-direction: column;
}

.autoprocesador-viewer .pdf-container {
    flex: 1;
    background: #2d3748;
    border-radius: 8px;
    overflow: auto;
}

/* Actions Panel */
.autoprocesador-actions {
    display: flex;
    flex-direction: column;
    overflow-y: auto;
}

.document-details {
    display: flex;
    flex-direction: column;
    gap: 15px;
}

.document-details.hidden {
    display: none;
}

.detail-group {
    display: flex;
    flex-direction: column;
    gap: 5px;
}

.detail-group label {
    font-size: 0.85rem;
    font-weight: 600;
    color: #4a5568;
}

.detail-input,
.detail-select {
    padding: 8px 12px;
    border: 1px solid #e2e8f0;
    border-radius: 6px;
    font-size: 0.9rem;
    background: white;
}

.detail-input:read-only {
    background: #f7fafc;
    color: #718096;
}

.detail-input.editable,
.detail-select.editable {
    border-color: #667eea;
    background: #f0f4ff;
}

.confidence-bar {
    position: relative;
    height: 30px;
    background: #e2e8f0;
    border-radius: 15px;
    overflow: hidden;
}

.confidence-fill {
    height: 100%;
    background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    transition: width 0.3s ease;
    display: flex;
    align-items: center;
    justify-content: center;
}

.confidence-text {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    font-weight: bold;
    color: #2d3748;
    font-size: 0.85rem;
}

.alert-info {
    background: #e6f7ff;
    border: 1px solid #91d5ff;
    border-radius: 6px;
    padding: 10px;
    font-size: 0.85rem;
    color: #096dd9;
}

.action-buttons {
    display: flex;
    flex-direction: column;
    gap: 10px;
    margin-top: 20px;
}

.btn-approve {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
    color: white;
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-approve:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3);
}

.btn-reject {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%);
    color: white;
    padding: 12px 20px;
    border: none;
    border-radius: 8px;
    font-weight: 600;
    cursor: pointer;
    transition: transform 0.2s;
}

.btn-reject:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(250, 112, 154, 0.3);
}

.no-selection {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    color: #a0aec0;
    text-align: center;
    padding: 20px;
}

.no-selection-icon {
    font-size: 4rem;
    margin-bottom: 15px;
    opacity: 0.5;
}

.no-selection.hidden {
    display: none;
}

.btn-secondary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 8px 16px;
    border: none;
    border-radius: 6px;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.2s;
}

.btn-secondary:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3);
}

/* Responsive */
@media (max-width: 1400px) {
    .autoprocesador-layout {
        grid-template-columns: 300px 1fr 350px;
    }
}

@media (max-width: 1024px) {
    .autoprocesador-layout {
        grid-template-columns: 1fr;
        grid-template-rows: auto auto 1fr;
    }
    
    .autoprocesador-stats {
        max-height: 300px;
    }
}
CSSEOF
    
    log_info "style.css actualizado correctamente"
}

# ============= PASO 3: ACTUALIZAR app.js =============

update_app_js() {
    log_step "PASO 3: Actualizando static/js/app.js"
    
    local app_js="${PROJECT_ROOT}/static/js/app.js"
    
    if [[ ! -f "${app_js}" ]]; then
        log_error "app.js no encontrado"
        return 1
    fi
    
    # Backup
    backup_file "${app_js}"
    
    # Verificar si ya existen las funciones
    if grep -q "AUTO-PROCESADOR FUNCTIONS" "${app_js}"; then
        log_warn "Las funciones de Auto-Procesador ya existen en app.js"
        return 0
    fi
    
    log_info "Añadiendo funciones JavaScript..."
    
    # Añadir al final del archivo
    cat >> "${app_js}" <<'JSEOF'

// ============================================
// AUTO-PROCESADOR FUNCTIONS
// ============================================

let currentDocumentId = null;
let autoProcesadorData = {
    stats: {},
    documents: [],
    clientes: []
};

// Cargar estadísticas y documentos
async function loadAutoProcesadorData() {
    try {
        const statsRes = await fetch('/api/autoprocesador/stats');
        const statsData = await statsRes.json();
        
        if (statsData.success) {
            autoProcesadorData.stats = statsData.stats;
            updateStatsDisplay();
        }
        
        const docsRes = await fetch('/api/autoprocesador/cola-revision');
        const docsData = await docsRes.json();
        
        if (docsData.success) {
            autoProcesadorData.documents = docsData.documentos;
            updateDocumentsList();
        }
        
        const clientesRes = await fetch('/api/autoprocesador/clientes');
        const clientesData = await clientesRes.json();
        
        if (clientesData.success) {
            autoProcesadorData.clientes = clientesData.clientes;
            updateClientesSelect();
        }
        
    } catch (error) {
        console.error('Error cargando datos:', error);
        showStatus('❌ Error cargando datos del auto-procesador', 'error');
    }
}

function updateStatsDisplay() {
    const stats = autoProcesadorData.stats;
    
    document.getElementById('stat-total').textContent = stats.total_hoy || 0;
    document.getElementById('stat-auto').textContent = stats.automaticos || 0;
    document.getElementById('stat-revision').textContent = stats.en_revision || 0;
    document.getElementById('stat-error').textContent = stats.errores || 0;
    
    document.getElementById('percent-auto').textContent = (stats.porcentaje_auto || 0) + '%';
    document.getElementById('percent-revision').textContent = (stats.porcentaje_revision || 0) + '%';
    document.getElementById('percent-error').textContent = (stats.porcentaje_errores || 0) + '%';
}

function updateDocumentsList() {
    const container = document.getElementById('documentsList');
    const docs = autoProcesadorData.documents;
    
    if (docs.length === 0) {
        container.innerHTML = '<p class="placeholder">No hay documentos en cola de revisión</p>';
        return;
    }
    
    container.innerHTML = docs.map(doc => `
        <div class="document-item" onclick="selectDocument(${doc.id})">
            <div class="document-item-header">
                <span class="document-item-name">${doc.archivo_original}</span>
                <span class="document-item-badge badge-${doc.estado}">
                    ${doc.estado === 'revision' ? '⚠️ Revisión' : doc.estado}
                </span>
            </div>
            <div class="document-item-info">
                <div>👤 ${doc.cliente_detectado || 'Sin detectar'}</div>
                <div>📋 ${doc.tipo_documento || 'Sin clasificar'}</div>
                <div>🎯 Confianza: ${Math.round((doc.confianza || 0) * 100)}%</div>
            </div>
        </div>
    `).join('');
}

function updateClientesSelect() {
    const select = document.getElementById('detail-cliente-select');
    const clientes = autoProcesadorData.clientes;
    
    select.innerHTML = '<option value="">-- Seleccionar cliente --</option>' +
        clientes.map(c => `<option value="${c.codigo}">${c.nombre}</option>`).join('');
}

async function selectDocument(docId) {
    currentDocumentId = docId;
    
    document.querySelectorAll('.document-item').forEach(item => {
        item.classList.remove('selected');
    });
    event.currentTarget.classList.add('selected');
    
    try {
        const res = await fetch(`/api/autoprocesador/documento/${docId}`);
        const data = await res.json();
        
        if (!data.success) {
            throw new Error(data.error);
        }
        
        const doc = data.documento;
        
        document.getElementById('noDocumentSelected').classList.add('hidden');
        document.getElementById('documentDetails').classList.remove('hidden');
        
        document.getElementById('detail-filename').value = doc.archivo_original;
        document.getElementById('detail-cliente').value = doc.cliente_detectado || '';
        document.getElementById('detail-cliente-select').value = doc.cliente_codigo || '';
        document.getElementById('detail-tipo').value = doc.tipo_documento || 'Otros';
        document.getElementById('detail-fecha').value = doc.fecha_documento || 'No detectada';
        document.getElementById('detail-carpeta').value = doc.carpeta_sugerida || 'No calculada';
        
        const confianza = Math.round((doc.confianza || 0) * 100);
        document.getElementById('detail-confianza-bar').style.width = confianza + '%';
        document.getElementById('detail-confianza-text').textContent = confianza + '%';
        
        const pdfViewer = document.getElementById('autoProcesadorPdfViewer');
        pdfViewer.innerHTML = `<embed src="/api/autoprocesador/pdf/${docId}" type="application/pdf" width="100%" height="100%">`;
        
    } catch (error) {
        console.error('Error cargando documento:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
}

async function aprobarDocumento() {
    if (!currentDocumentId) return;
    
    if (!confirm('¿Aprobar y guardar este documento en su ubicación definitiva?')) {
        return;
    }
    
    try {
        const clienteSelect = document.getElementById('detail-cliente-select');
        const tipoSelect = document.getElementById('detail-tipo');
        
        const payload = {
            usuario_modifico: true,
            cliente_codigo: clienteSelect.value,
            tipo_documento: tipoSelect.value
        };
        
        const res = await fetch(`/api/autoprocesador/aprobar/${currentDocumentId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        
        const data = await res.json();
        
        if (data.success) {
            showStatus('✅ Documento aprobado: ' + data.ruta_destino, 'success');
            
            await loadAutoProcesadorData();
            
            currentDocumentId = null;
            document.getElementById('documentDetails').classList.add('hidden');
            document.getElementById('noDocumentSelected').classList.remove('hidden');
            document.getElementById('autoProcesadorPdfViewer').innerHTML = 
                '<p class="placeholder">Selecciona un documento de la lista para ver detalles</p>';
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error aprobando documento:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
}

async function rechazarDocumento() {
    if (!currentDocumentId) return;
    
    const motivo = prompt('¿Por qué rechazas este documento?', 'Documento ilegible o incorrecto');
    if (!motivo) return;
    
    try {
        const res = await fetch(`/api/autoprocesador/rechazar/${currentDocumentId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ motivo })
        });
        
        const data = await res.json();
        
        if (data.success) {
            showStatus('⚠️ Documento rechazado', 'warning');
            
            await loadAutoProcesadorData();
            
            currentDocumentId = null;
            document.getElementById('documentDetails').classList.add('hidden');
            document.getElementById('noDocumentSelected').classList.remove('hidden');
            document.getElementById('autoProcesadorPdfViewer').innerHTML = 
                '<p class="placeholder">Selecciona un documento de la lista para ver detalles</p>';
        } else {
            throw new Error(data.error);
        }
        
    } catch (error) {
        console.error('Error rechazando documento:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
}

function refreshAutoProcesadorStats() {
    loadAutoProcesadorData();
    showStatus('🔄 Datos actualizados', 'success');
}

async function showAllProcessed() {
    try {
        const res = await fetch('/api/autoprocesador/procesados-hoy');
        const data = await res.json();
        
        if (data.success) {
            const docs = data.documentos;
            const container = document.getElementById('documentsList');
            
            if (docs.length === 0) {
                container.innerHTML = '<p class="placeholder">No se han procesado documentos hoy</p>';
                return;
            }
            
            container.innerHTML = docs.map(doc => `
                <div class="document-item">
                    <div class="document-item-header">
                        <span class="document-item-name">${doc.archivo_original}</span>
                        <span class="document-item-badge badge-${doc.estado}">
                            ${doc.estado === 'auto' ? '✅ Auto' : doc.estado}
                        </span>
                    </div>
                    <div class="document-item-info">
                        <div>👤 ${doc.cliente_detectado || 'N/A'}</div>
                        <div>📋 ${doc.tipo_documento || 'N/A'}</div>
                        <div>📁 ${doc.ruta_definitiva || 'Pendiente'}</div>
                    </div>
                </div>
            `).join('');
        }
    } catch (error) {
        console.error('Error:', error);
        showStatus('❌ Error cargando procesados', 'error');
    }
}

// Modificar switchTab para incluir autoprocesador
(function() {
    const originalSwitchTab = window.switchTab;
    window.switchTab = function(tabName) {
        if (typeof originalSwitchTab === 'function') {
            originalSwitchTab(tabName);
        } else {
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab-btn').forEach(btn => {
                btn.classList.remove('active');
            });
            
            const selectedTab = document.getElementById(`tab-${tabName}`);
            if (selectedTab) {
                selectedTab.classList.add('active');
            }
            
            event.currentTarget.classList.add('active');
        }
        
        if (tabName === 'autoprocesador') {
            loadAutoProcesadorData();
        }
    };
})();
JSEOF
    
    log_info "app.js actualizado correctamente"
}

# ============= VERIFICACIÓN FINAL =============

verify_integration() {
    log_step "Verificando integración..."
    
    local errors=0
    
    # Verificar archivos modificados
    if grep -q "tab-autoprocesador" "${PROJECT_ROOT}/templates/index.html"; then
        log_info "✓ index.html contiene el nuevo tab"
    else
        log_error "✗ index.html NO contiene el nuevo tab"
        ((errors++))
    fi
    
    if grep -q "AUTO-PROCESADOR STYLES" "${PROJECT_ROOT}/static/css/style.css"; then
        log_info "✓ style.css contiene los nuevos estilos"
    else
        log_error "✗ style.css NO contiene los nuevos estilos"
        ((errors++))
    fi
    
    if grep -q "AUTO-PROCESADOR FUNCTIONS" "${PROJECT_ROOT}/static/js/app.js"; then
        log_info "✓ app.js contiene las nuevas funciones"
    else
        log_error "✗ app.js NO contiene las nuevas funciones"
        ((errors++))
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
    update_index_html || exit 1
    update_style_css || exit 1
    update_app_js || exit 1
    verify_integration || exit 1
    
    echo
    echo -e "${GREEN}===============================================${NC}"
    echo -e "${GREEN}  ✓ INTEGRACIÓN COMPLETADA CON ÉXITO${NC}"
    echo -e "${GREEN}===============================================${NC}"
    echo
    echo -e "📦 Backups guardados en: ${YELLOW}${BACKUP_DIR}${NC}"
    echo
    echo -e "${BLUE}Archivos modificados:${NC}"
    echo -e "  • ${GREEN}templates/index.html${NC} → Añadida 4ª pestaña"
    echo -e "  • ${GREEN}static/css/style.css${NC} → Añadidos estilos"
    echo -e "  • ${GREEN}static/js/app.js${NC} → Añadidas funciones JS"
    echo
    echo -e "${BLUE}Para ver los cambios:${NC}"
    echo -e "  ${GREEN}1.${NC} Reinicia el servidor: ${YELLOW}python run.py${NC}"
    echo -e "  ${GREEN}2.${NC} Abre: ${YELLOW}http://localhost:5001${NC}"
    echo -e "  ${GREEN}3.${NC} Haz clic en: ${YELLOW}🤖 Auto-Procesador${NC}"
    echo
    echo -e "${YELLOW}💡 Nota:${NC} Si el navegador muestra la versión anterior,"
    echo -e "   presiona ${YELLOW}Cmd+Shift+R${NC} (Mac) o ${YELLOW}Ctrl+F5${NC} (Win) para forzar recarga."
    echo
}

main "$@"
