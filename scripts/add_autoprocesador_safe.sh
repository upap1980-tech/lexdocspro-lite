#!/usr/bin/env bash
# add_autoprocesador_safe.sh - INTEGRACIÓN SEGURA Y DEFINITIVA

set -euo pipefail

PROJECT_ROOT="$(pwd)"
BACKUP_DIR="${PROJECT_ROOT}/_safe_backup_$(date +%Y%m%d_%H%M%S)"

echo "🎯 INTEGRACIÓN SEGURA DEL AUTO-PROCESADOR"
echo "=========================================="
echo ""

mkdir -p "${BACKUP_DIR}"

# ============================================
# BACKUPS
# ============================================
echo "📦 Creando backups..."
cp templates/index.html "${BACKUP_DIR}/"
cp static/css/style.css "${BACKUP_DIR}/"
cp static/js/app.js "${BACKUP_DIR}/"
echo "✓ Backups en: ${BACKUP_DIR}"
echo ""

# ============================================
# PASO 1: HTML - Añadir botón de pestaña
# ============================================
echo "🔧 PASO 1: Añadiendo botón de pestaña..."

if grep -q "Auto-Procesador" templates/index.html; then
    echo "⚠️ Botón ya existe, saltando..."
else
    # Buscar la línea del botón LexNET y añadir después
    sed -i.bak '/Analizador LexNET/a\
            <button class="tab-btn" onclick="switchTab('"'"'autoprocesador'"'"')">🤖 Auto-Procesador</button>' \
        templates/index.html
    
    rm -f templates/index.html.bak
    echo "✓ Botón añadido"
fi

# ============================================
# PASO 2: HTML - Añadir contenido del tab
# ============================================
echo ""
echo "🔧 PASO 2: Añadiendo contenido del tab..."

if grep -q 'id="tab-autoprocesador"' templates/index.html; then
    echo "⚠️ Contenido del tab ya existe, saltando..."
else
    # Encontrar la línea del footer y añadir antes
    python3 <<'PYSCRIPT'
import sys

with open('templates/index.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Buscar la línea con <footer>
footer_index = -1
for i, line in enumerate(lines):
    if '<footer>' in line:
        footer_index = i
        break

if footer_index == -1:
    print("❌ No se encontró <footer>")
    sys.exit(1)

# Contenido del nuevo tab
new_tab_content = '''
        <!-- TAB 4: AUTO-PROCESADOR -->
        <div id="tab-autoprocesador" class="tab-content">
            <div class="autoprocesador-layout">
                <!-- Panel Izquierdo -->
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
                
                <!-- Panel Central -->
                <div class="panel autoprocesador-viewer">
                    <h2>👁️ Vista Previa</h2>
                    <div id="autoProcesadorPdfViewer" class="pdf-container">
                        <p class="placeholder">Selecciona un documento</p>
                    </div>
                </div>
                
                <!-- Panel Derecho -->
                <div class="panel autoprocesador-actions">
                    <h2>📝 Detalles</h2>
                    <div id="documentDetails" class="document-details hidden">
                        <div class="detail-group">
                            <label>📄 Archivo:</label>
                            <input type="text" id="detail-filename" readonly class="detail-input">
                        </div>
                        <div class="detail-group">
                            <label>👤 Cliente:</label>
                            <input type="text" id="detail-cliente" class="detail-input editable">
                            <select id="detail-cliente-select" class="detail-select">
                                <option value="">-- Seleccionar --</option>
                            </select>
                        </div>
                        <div class="detail-group">
                            <label>📋 Tipo:</label>
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
                            <label>📅 Fecha:</label>
                            <input type="text" id="detail-fecha" readonly class="detail-input">
                        </div>
                        <div class="detail-group">
                            <label>📁 Carpeta:</label>
                            <input type="text" id="detail-carpeta" readonly class="detail-input">
                        </div>
                        <div class="detail-group">
                            <label>🎯 Confianza:</label>
                            <div class="confidence-bar">
                                <div id="detail-confianza-bar" class="confidence-fill"></div>
                                <span id="detail-confianza-text" class="confidence-text">0%</span>
                            </div>
                        </div>
                        <div class="alert-info">
                            <strong>💡 Nota:</strong> Modifica antes de aprobar
                        </div>
                        <div class="action-buttons">
                            <button onclick="aprobarDocumento()" class="btn-approve">✅ Aprobar</button>
                            <button onclick="rechazarDocumento()" class="btn-reject">❌ Rechazar</button>
                        </div>
                    </div>
                    <div id="noDocumentSelected" class="no-selection">
                        <div class="no-selection-icon">📄</div>
                        <p>Selecciona un documento</p>
                    </div>
                </div>
            </div>
        </div>

'''

# Insertar el nuevo contenido antes del footer
lines.insert(footer_index, new_tab_content)

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.writelines(lines)

print("✓ Contenido del tab añadido")
PYSCRIPT
fi

# ============================================
# PASO 3: CSS
# ============================================
echo ""
echo "🎨 PASO 3: Añadiendo estilos CSS..."

if grep -q "AUTO-PROCESADOR STYLES" static/css/style.css; then
    echo "⚠️ Estilos ya existen, saltando..."
else
    cat >> static/css/style.css <<'CSSEOF'

/* ============================================
   AUTO-PROCESADOR STYLES
   ============================================ */
.autoprocesador-layout {
    display: grid;
    grid-template-columns: 350px 1fr 400px;
    gap: 15px;
    height: calc(100vh - 200px);
}

.autoprocesador-stats { display: flex; flex-direction: column; overflow-y: auto; }
.stats-cards { display: grid; gap: 12px; margin-bottom: 15px; }
.stat-card {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px; padding: 15px; display: flex; align-items: center;
    gap: 12px; color: white; box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    transition: transform 0.2s;
}
.stat-card:hover { transform: translateY(-2px); box-shadow: 0 6px 12px rgba(0,0,0,0.15); }
.stat-card.stat-auto { background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); }
.stat-card.stat-revision { background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); }
.stat-card.stat-error { background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); }
.stat-icon { font-size: 2.5rem; opacity: 0.9; }
.stat-info { flex: 1; }
.stat-value { font-size: 2rem; font-weight: bold; line-height: 1; }
.stat-label { font-size: 0.85rem; opacity: 0.9; margin-top: 4px; }
.stat-percent { font-size: 0.75rem; opacity: 0.8; margin-top: 2px; }
.stats-actions { display: flex; gap: 10px; margin-bottom: 20px; }
.stats-actions button { flex: 1; }
.documents-list { flex: 1; overflow-y: auto; background: #f8f9fa; border-radius: 8px; padding: 10px; }
.document-item {
    background: white; border-radius: 8px; padding: 12px; margin-bottom: 10px;
    cursor: pointer; border: 2px solid transparent; transition: all 0.2s;
}
.document-item:hover { border-color: #667eea; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.2); }
.document-item.selected { border-color: #667eea; background: #f0f4ff; }
.document-item-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.document-item-name { font-weight: 600; color: #2d3748; font-size: 0.9rem; }
.document-item-badge { padding: 3px 8px; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
.badge-revision { background: #fff3cd; color: #856404; }
.badge-auto { background: #d4edda; color: #155724; }
.badge-error { background: #f8d7da; color: #721c24; }
.document-item-info { font-size: 0.8rem; color: #718096; }
.autoprocesador-viewer { display: flex; flex-direction: column; }
.autoprocesador-viewer .pdf-container { flex: 1; background: #2d3748; border-radius: 8px; overflow: auto; }
.autoprocesador-actions { display: flex; flex-direction: column; overflow-y: auto; }
.document-details { display: flex; flex-direction: column; gap: 15px; }
.document-details.hidden { display: none; }
.detail-group { display: flex; flex-direction: column; gap: 5px; }
.detail-group label { font-size: 0.85rem; font-weight: 600; color: #4a5568; }
.detail-input, .detail-select {
    padding: 8px 12px; border: 1px solid #e2e8f0; border-radius: 6px;
    font-size: 0.9rem; background: white;
}
.detail-input:read-only { background: #f7fafc; color: #718096; }
.detail-input.editable, .detail-select.editable { border-color: #667eea; background: #f0f4ff; }
.confidence-bar { position: relative; height: 30px; background: #e2e8f0; border-radius: 15px; overflow: hidden; }
.confidence-fill {
    height: 100%; background: linear-gradient(90deg, #11998e 0%, #38ef7d 100%);
    transition: width 0.3s ease; width: 0%;
}
.confidence-text {
    position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
    font-weight: bold; color: #2d3748; font-size: 0.85rem;
}
.alert-info { background: #e6f7ff; border: 1px solid #91d5ff; border-radius: 6px; padding: 10px; font-size: 0.85rem; color: #096dd9; }
.action-buttons { display: flex; flex-direction: column; gap: 10px; margin-top: 20px; }
.btn-approve {
    background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%); color: white;
    padding: 12px 20px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: transform 0.2s;
}
.btn-approve:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(17, 153, 142, 0.3); }
.btn-reject {
    background: linear-gradient(135deg, #fa709a 0%, #fee140 100%); color: white;
    padding: 12px 20px; border: none; border-radius: 8px; font-weight: 600; cursor: pointer; transition: transform 0.2s;
}
.btn-reject:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(250, 112, 154, 0.3); }
.no-selection {
    display: flex; flex-direction: column; align-items: center; justify-content: center;
    height: 100%; color: #a0aec0; text-align: center; padding: 20px;
}
.no-selection-icon { font-size: 4rem; margin-bottom: 15px; opacity: 0.5; }
.no-selection.hidden { display: none; }
.btn-secondary {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white;
    padding: 8px 16px; border: none; border-radius: 6px; font-weight: 600; cursor: pointer; transition: all 0.2s;
}
.btn-secondary:hover { transform: translateY(-2px); box-shadow: 0 4px 8px rgba(102, 126, 234, 0.3); }

@media (max-width: 1400px) {
    .autoprocesador-layout { grid-template-columns: 300px 1fr 350px; }
}
@media (max-width: 1024px) {
    .autoprocesador-layout { grid-template-columns: 1fr; grid-template-rows: auto auto 1fr; }
    .autoprocesador-stats { max-height: 300px; }
}
CSSEOF
    echo "✓ Estilos CSS añadidos"
fi

# ============================================
# PASO 4: JavaScript - HOOK NO INVASIVO
# ============================================
echo ""
echo "⚡ PASO 4: Añadiendo JavaScript..."

if grep -q "AUTO-PROCESADOR FUNCTIONS" static/js/app.js; then
    echo "⚠️ Funciones JS ya existen, saltando..."
else
    cat >> static/js/app.js <<'JSEOF'

// ============================================
// AUTO-PROCESADOR FUNCTIONS
// ============================================

let currentDocumentId = null;
let autoProcesadorData = { stats: {}, documents: [], clientes: [] };

// Hook en switchTab EXISTENTE sin modificarlo
(function() {
    const originalSwitchTab = window.switchTab;
    if (typeof originalSwitchTab === 'function') {
        window.switchTab = function(tabName) {
            originalSwitchTab.call(this, tabName);
            if (tabName === 'autoprocesador') {
                setTimeout(() => loadAutoProcesadorData(), 100);
            }
        };
    }
})();

async function loadAutoProcesadorData() {
    try {
        const [statsRes, docsRes, clientesRes] = await Promise.all([
            fetch('/api/autoprocesador/stats'),
            fetch('/api/autoprocesador/cola-revision'),
            fetch('/api/autoprocesador/clientes')
        ]);
        
        const statsData = await statsRes.json();
        const docsData = await docsRes.json();
        const clientesData = await clientesRes.json();
        
        if (statsData.success) {
            autoProcesadorData.stats = statsData.stats;
            updateStatsDisplay();
        }
        
        if (docsData.success) {
            autoProcesadorData.documents = docsData.documentos;
            updateDocumentsList();
        }
        
        if (clientesData.success) {
            autoProcesadorData.clientes = clientesData.clientes;
            updateClientesSelect();
        }
    } catch (error) {
        console.error('Error cargando auto-procesador:', error);
    }
}

function updateStatsDisplay() {
    const s = autoProcesadorData.stats;
    document.getElementById('stat-total').textContent = s.total_hoy || 0;
    document.getElementById('stat-auto').textContent = s.automaticos || 0;
    document.getElementById('stat-revision').textContent = s.en_revision || 0;
    document.getElementById('stat-error').textContent = s.errores || 0;
    document.getElementById('percent-auto').textContent = (s.porcentaje_auto || 0) + '%';
    document.getElementById('percent-revision').textContent = (s.porcentaje_revision || 0) + '%';
    document.getElementById('percent-error').textContent = (s.porcentaje_errores || 0) + '%';
}

function updateDocumentsList() {
    const container = document.getElementById('documentsList');
    const docs = autoProcesadorData.documents;
    
    if (docs.length === 0) {
        container.innerHTML = '<p class="placeholder">No hay documentos en cola</p>';
        return;
    }
    
    container.innerHTML = docs.map(doc => `
        <div class="document-item" onclick="selectDocument(${doc.id})">
            <div class="document-item-header">
                <span class="document-item-name">${doc.archivo_original}</span>
                <span class="document-item-badge badge-${doc.estado}">⚠️ Revisión</span>
            </div>
            <div class="document-item-info">
                <div>👤 ${doc.cliente_detectado || 'Sin detectar'}</div>
                <div>📋 ${doc.tipo_documento || 'Sin clasificar'}</div>
                <div>🎯 ${Math.round((doc.confianza || 0) * 100)}%</div>
            </div>
        </div>
    `).join('');
}

function updateClientesSelect() {
    const select = document.getElementById('detail-cliente-select');
    select.innerHTML = '<option value="">-- Seleccionar --</option>' +
        autoProcesadorData.clientes.map(c => `<option value="${c.codigo}">${c.nombre}</option>`).join('');
}

async function selectDocument(docId) {
    currentDocumentId = docId;
    document.querySelectorAll('.document-item').forEach(i => i.classList.remove('selected'));
    event.currentTarget.classList.add('selected');
    
    try {
        const res = await fetch(`/api/autoprocesador/documento/${docId}`);
        const data = await res.json();
        if (!data.success) throw new Error(data.error);
        
        const doc = data.documento;
        document.getElementById('noDocumentSelected').classList.add('hidden');
        document.getElementById('documentDetails').classList.remove('hidden');
        document.getElementById('detail-filename').value = doc.archivo_original;
        document.getElementById('detail-cliente').value = doc.cliente_detectado || '';
        document.getElementById('detail-cliente-select').value = doc.cliente_codigo || '';
        document.getElementById('detail-tipo').value = doc.tipo_documento || 'Otros';
        document.getElementById('detail-fecha').value = doc.fecha_documento || 'N/A';
        document.getElementById('detail-carpeta').value = doc.carpeta_sugerida || 'N/A';
        
        const confianza = Math.round((doc.confianza || 0) * 100);
        document.getElementById('detail-confianza-bar').style.width = confianza + '%';
        document.getElementById('detail-confianza-text').textContent = confianza + '%';
        
        document.getElementById('autoProcesadorPdfViewer').innerHTML = 
            `<embed src="/api/autoprocesador/pdf/${docId}" type="application/pdf" width="100%" height="100%">`;
    } catch (error) {
        console.error('Error:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
}

async function aprobarDocumento() {
    if (!currentDocumentId || !confirm('¿Aprobar documento?')) return;
    
    try {
        const res = await fetch(`/api/autoprocesador/aprobar/${currentDocumentId}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({
                usuario_modifico: true,
                cliente_codigo: document.getElementById('detail-cliente-select').value,
                tipo_documento: document.getElementById('detail-tipo').value
            })
        });
        
        const data = await res.json();
        if (data.success) {
            showStatus('✅ Documento aprobado', 'success');
            await loadAutoProcesadorData();
            currentDocumentId = null;
            document.getElementById('documentDetails').classList.add('hidden');
            document.getElementById('noDocumentSelected').classList.remove('hidden');
            document.getElementById('autoProcesadorPdfViewer').innerHTML = '<p class="placeholder">Selecciona un documento</p>';
        } else throw new Error(data.error);
    } catch (error) {
        console.error('Error:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
}

async function rechazarDocumento() {
    if (!currentDocumentId) return;
    const motivo = prompt('¿Por qué rechazas?', 'Ilegible');
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
            document.getElementById('autoProcesadorPdfViewer').innerHTML = '<p class="placeholder">Selecciona un documento</p>';
        } else throw new Error(data.error);
    } catch (error) {
        console.error('Error:', error);
        showStatus('❌ Error: ' + error.message, 'error');
    }
}

function refreshAutoProcesadorStats() {
    loadAutoProcesadorData();
    showStatus('🔄 Actualizado', 'success');
}

async function showAllProcessed() {
    try {
        const res = await fetch('/api/autoprocesador/procesados-hoy');
        const data = await res.json();
        if (!data.success) return;
        
        const docs = data.documentos;
        const container = document.getElementById('documentsList');
        
        if (docs.length === 0) {
            container.innerHTML = '<p class="placeholder">Sin documentos procesados hoy</p>';
            return;
        }
        
        container.innerHTML = docs.map(doc => `
            <div class="document-item">
                <div class="document-item-header">
                    <span class="document-item-name">${doc.archivo_original}</span>
                    <span class="document-item-badge badge-${doc.estado}">✅ ${doc.estado}</span>
                </div>
                <div class="document-item-info">
                    <div>👤 ${doc.cliente_detectado || 'N/A'}</div>
                    <div>📋 ${doc.tipo_documento || 'N/A'}</div>
                </div>
            </div>
        `).join('');
    } catch (error) {
        console.error('Error:', error);
    }
}
JSEOF
    echo "✓ Funciones JavaScript añadidas"
fi

# ============================================
# VERIFICACIÓN
# ============================================
echo ""
echo "🔍 Verificando integración..."

errors=0

if grep -q "Auto-Procesador" templates/index.html; then
    echo "✓ Botón presente"
else
    echo "✗ Botón NO encontrado"
    ((errors++))
fi

if grep -q 'id="tab-autoprocesador"' templates/index.html; then
    echo "✓ Contenido HTML presente"
else
    echo "✗ Contenido HTML NO encontrado"
    ((errors++))
fi

if grep -q "AUTO-PROCESADOR STYLES" static/css/style.css; then
    echo "✓ Estilos CSS presentes"
else
    echo "✗ Estilos CSS NO encontrados"
    ((errors++))
fi

if grep -q "AUTO-PROCESADOR FUNCTIONS" static/js/app.js; then
    echo "✓ Funciones JS presentes"
else
    echo "✗ Funciones JS NO encontradas"
    ((errors++))
fi

echo ""
if [[ ${errors} -eq 0 ]]; then
    echo "✅ INTEGRACIÓN COMPLETADA EXITOSAMENTE"
    echo ""
    echo "📋 Siguiente:"
    echo "  1. Reinicia Flask: python run.py"
    echo "  2. Recarga navegador: Cmd+Shift+R"
    echo "  3. Verifica que las 4 pestañas funcionen"
    echo ""
    echo "💾 Backups en: ${BACKUP_DIR}"
else
    echo "⚠️ Encontrados ${errors} errores"
fi
