// ============================================
// ESTADO GLOBAL
// ============================================
let currentFile = null;
let ocrText = '';
let availableProviders = [];
let currentDocType = null;
let generatedDocContent = '';
let uploadedFiles = [];
let processedTexts = [];
let currentAnalysis = '';

// ============================================
// INICIALIZACIÓN
// ============================================
document.addEventListener('DOMContentLoaded', () => {
    // Inicializar tab de consultas
    refreshFiles();
    loadAIProviders();
    addMessage('system', '¡Bienvenido a LexDocsPro LITE v2.0! Ahora con múltiples IAs y generación de documentos.');

    // Inicializar generador de documentos
    loadDocumentTemplates();

    // Inicializar drag & drop para LexNET
    initializeLexNetUploader();

    // Event listener para Enter en chat
    const promptInput = document.getElementById('chatPrompt');
    if (promptInput) {
        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
    }
});

// ============================================
// GESTIÓN DE TABS
// ============================================
function switchTab(tabName) {
    // Desactivar todos los tabs
    document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
    document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

    // Activar tab seleccionado
    const clickedBtn = event ? event.target : null;
    if (clickedBtn && clickedBtn.classList.contains('tab-btn')) {
        clickedBtn.classList.add('active');
    }

    const content = document.getElementById(`tab-${tabName}`);
    if (content) content.classList.add('active');

    updateStatus(`Pestaña: ${tabName}`);
}

// Compatibilidad con Sidebar v2.3.1
window.switchPanel = function (panelId) {
    console.log(`Cambiando a panel: ${panelId}`);

    // Ocultar todos los paneles
    document.querySelectorAll('.panel').forEach(p => p.classList.remove('active'));

    // Mostrar el seleccionado
    const panel = document.getElementById(`panel-${panelId}`);
    if (panel) {
        panel.classList.add('active');

        // Actualizar título del header
        const headerTitle = document.getElementById('headerTitle');
        if (headerTitle) {
            const navItem = document.querySelector(`.nav-item[data-panel="${panelId}"]`);
            headerTitle.textContent = navItem ? navItem.innerText.trim() : panelId.charAt(0).toUpperCase() + panelId.slice(1);
        }
    } else {
        // Si el panel no existe en la estructura de index.html, intentar switchTab si es una feature antigua
        switchTab(panelId);
    }

    // ═══════════════════════════════════════════════════════════════
    // TRIGGERS DE CARGA DINÁMICA POR PANEL
    // ═══════════════════════════════════════════════════════════════

    function showPanel(panelId) {
        // Ocultar todos los paneles
        document.querySelectorAll('.section').forEach(s => s.classList.remove('active'));
        
        // Mostrar panel seleccionado
        const panel = document.getElementById(panelId);
        if (panel) panel.classList.add('active');
        
        // Triggers de carga dinámica por panel
        if (panelId === 'ia-cascade') loadCascadeStats();  // ⚠️ CAMBIO: 'cascade' → 'ia-cascade'
        if (panelId === 'banking') loadBankingStats();
        if (panelId === 'analytics') updateAnalytics();
        if (panelId === 'agent') initializeAgentCoordinator();
    }

    // ═══════════════════════════════════════════════════════════════
    // IA CASCADE FUNCTIONS v3.0
    // ═══════════════════════════════════════════════════════════════

    let currentProviderForKey = null;

    /**
     * Cargar estadísticas de IA Cascade
     * Actualiza stats globales y tabla de providers
     */
    async function loadCascadeStats() {
        try {
            const response = await fetch('/api/ia-cascade/stats-public');
            const data = await response.json();
            
            if (data.success) {
                const stats = data.stats;
                
                // ========== STATS GLOBALES ==========
                const totalCalls = stats.global.total_calls || 0;
                const successCalls = stats.global.successful_calls || 0;
                const failedCalls = stats.global.failed_calls || 0;
                const avgUptime = stats.global.avg_uptime || 0;
                const enabledProviders = stats.global.enabled_providers || 0;
                
                // Actualizar DOM
                setElementText('cascade-total-calls', totalCalls);
                setElementText('cascade-success-calls', successCalls);
                setElementText('cascade-failed-calls', failedCalls);
                setElementText('cascade-avg-uptime', avgUptime.toFixed(2) + '%');
                setElementText('cascade-enabled-providers', enabledProviders);
                
                // ========== CARGAR TABLA DE PROVIDERS ==========
                await loadProvidersTable(stats.providers);
                
                console.log('✅ IA Cascade stats cargadas:', stats);
            } else {
                console.error('❌ Error cargando stats:', data.error);
            }
        } catch (error) {
            console.error('❌ Error en loadCascadeStats:', error);
        }
    }

    /**
     * Cargar tabla de providers con configuración y stats
     */
    async function loadProvidersTable(statsProviders) {
        try {
            const response = await fetch('/api/ia-cascade/providers-public');
            const data = await response.json();
            
            if (data.success) {
                const providers = data.providers;
                const tbody = document.getElementById('providers-tbody');
                
                if (!tbody) {
                    console.warn('⚠️ Elemento providers-tbody no encontrado');
                    return;
                }
                
                tbody.innerHTML = '';
                
                // Ordenar providers por prioridad
                const sortedProviders = Object.entries(providers).sort((a, b) => a[1].priority - b[1].priority);
                
                sortedProviders.forEach(([provider_id, config]) => {
                    const providerStats = statsProviders[provider_id] || {};
                    
                    const row = document.createElement('tr');
                    row.className = config.enabled ? 'provider-enabled' : 'provider-disabled';
                    
                    // Construir HTML de la fila
                    row.innerHTML = `
                        <td>${config.priority}</td>
                        <td>
                            <strong>${config.name}</strong>
                            ${config.local ? '🏠' : '☁️'}
                        </td>
                        <td><code style="font-size: 0.85em;">${config.model}</code></td>
                        <td>
                            <span class="status-badge ${config.enabled ? 'status-enabled' : 'status-disabled'}">
                                ${config.enabled ? '✅ Enabled' : '❌ Disabled'}
                            </span>
                        </td>
                        <td>${providerStats.total_calls || 0}</td>
                        <td style="color: #38a169; font-weight: 600;">${providerStats.successful_calls || 0}</td>
                        <td style="color: #e53e3e; font-weight: 600;">${providerStats.failed_calls || 0}</td>
                        <td>${providerStats.avg_time ? providerStats.avg_time.toFixed(2) + 's' : 'N/A'}</td>
                        <td>
                            <div class="uptime-bar">
                                <div class="uptime-fill" style="width: ${providerStats.uptime_percentage || 0}%"></div>
                                <span>${(providerStats.uptime_percentage || 0).toFixed(1)}%</span>
                            </div>
                        </td>
                        <td>
                            ${config.has_api_key 
                                ? '<span class="badge-success">✅ Configurada</span>' 
                                : '<span class="badge-warning">⚠️ No configurada</span>'
                            }
                        </td>
                        <td class="actions-cell">
                            <button class="btn-icon" onclick="toggleProvider('${provider_id}', ${!config.enabled})" 
                                    title="${config.enabled ? 'Deshabilitar' : 'Habilitar'}">
                                ${config.enabled ? '⏸️' : '▶️'}
                            </button>
                            ${!config.local ? `
                                <button class="btn-icon" onclick="openAPIKeyModal('${provider_id}')" title="Actualizar API Key">
                                    🔑
                                </button>
                            ` : ''}
                            <button class="btn-icon" onclick="testProvider('${provider_id}')" title="Test rápido">
                                🧪
                            </button>
                        </td>
                    `;
                    
                    tbody.appendChild(row);
                });
                
                console.log(`✅ Tabla de providers cargada (${sortedProviders.length} providers)`);
            } else {
                console.error('❌ Error cargando providers:', data.error);
            }
        } catch (error) {
            console.error('❌ Error en loadProvidersTable:', error);
        }
    }

    /**
     * Test de IA Cascade con provider seleccionado
     */
    async function testIACascade() {
        const btn = document.getElementById('btn-test-cascade');
        const provider = document.getElementById('test-provider').value;
        const temperature = parseFloat(document.getElementById('test-temperature').value);
        const prompt = document.getElementById('test-prompt-input').value.trim();
        
        if (!prompt) {
            alert('❌ Escribe un prompt de prueba');
            return;
        }
        
        // UI Loading
        btn.disabled = true;
        btn.innerHTML = '<span class="loading"></span> Ejecutando...';
        document.getElementById('test-result').style.display = 'none';
        document.getElementById('test-error').style.display = 'none';
        
        console.log('🧪 Ejecutando test:', { provider, temperature, prompt: prompt.substring(0, 50) + '...' });
        
        try {
            const response = await fetch('/api/ia-cascade/test', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider: provider,
                    temperature: temperature,
                    prompt: prompt
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                // ========== MOSTRAR RESULTADO ==========
                setElementText('result-provider', data.provider_used || 'N/A');
                setElementText('result-time', data.time ? data.time.toFixed(2) + 's' : 'N/A');
                setElementText('result-tokens', data.metadata?.tokens || 'N/A');
                setElementText('result-text', data.response || '');
                
                document.getElementById('test-result').style.display = 'block';
                
                console.log('✅ Test exitoso:', {
                    provider: data.provider_used,
                    time: data.time,
                    tokens: data.metadata?.tokens,
                    response_length: data.response?.length
                });
            } else {
                // ========== MOSTRAR ERROR ==========
                setElementText('error-text', data.error || 'Error desconocido');
                document.getElementById('test-error').style.display = 'block';
                
                console.error('❌ Test fallido:', data.error);
            }
        } catch (error) {
            setElementText('error-text', error.message);
            document.getElementById('test-error').style.display = 'block';
            
            console.error('❌ Error en test:', error);
        } finally {
            btn.disabled = false;
            btn.innerHTML = '🚀 Ejecutar Test';
        }
    }

    /**
     * Test rápido de un provider específico
     */
    async function testProvider(provider_id) {
        document.getElementById('test-provider').value = provider_id;
        await testIACascade();
    }

    /**
     * Toggle provider (habilitar/deshabilitar)
     */
    async function toggleProvider(provider_id, enabled) {
        try {
            console.log(`🔄 Toggle provider: ${provider_id} → ${enabled ? 'enabled' : 'disabled'}`);
            
            const response = await fetch('/api/ia-cascade/toggle-provider', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    provider_id: provider_id,
                    enabled: enabled
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                console.log(`✅ Provider ${provider_id} ${enabled ? 'habilitado' : 'deshabilitado'}`);
                await loadCascadeStats();  // Refrescar tabla
            } else {
                alert('❌ Error: ' + data.error);
            }
        } catch (error) {
            console.error('❌ Error toggling provider:', error);
            alert('❌ Error: ' + error.message);
        }
    }

    /**
     * Abrir modal para actualizar API key
     */
    function openAPIKeyModal(provider_id) {
        currentProviderForKey = provider_id;
        setElementText('modal-provider-name', provider_id.toUpperCase());
        document.getElementById('modal-api-key-input').value = '';
        document.getElementById('api-key-modal').classList.add('visible');
        
        console.log('🔑 Modal abierto para:', provider_id);
    }

    /**
     * Cerrar modal de API key
     */
    function closeAPIKeyModal() {
        document.getElementById('api-key-modal').classList.remove('visible');
        currentProviderForKey = null;
    }

    /**
     * Guardar API key del provider
     */
    async function saveAPIKey() {
        const api_key = document.getElementById('modal-api-key-input').value.trim();
        
        if (!api_key) {
            alert('❌ Ingresa una API key válida');
            return;
        }
        
        try {
            con


// ============================================
// PROVEEDORES DE IA
// ============================================
async function loadAIProviders() {
    try {
        const response = await fetch('/api/ai/providers');
        const data = await response.json();

        availableProviders = data.providers;
        const selects = [
            document.getElementById('aiProvider'),
            document.getElementById('docProvider'),
            document.getElementById('lexnetProvider')
        ];

        const providerNames = {
            'ollama': '🏠 Ollama (Local)',
            'groq': '⚡ Groq (Ultra Rápido)',
            'openai': '🤖 ChatGPT (OpenAI)',
            'perplexity': '🔍 Perplexity',
            'gemini': '💎 Gemini (Google)',
            'deepseek': '🌊 DeepSeek'
        };

        selects.forEach(select => {
            if (select) {
                select.innerHTML = '';
                availableProviders.forEach(provider => {
                    const option = document.createElement('option');
                    option.value = provider;
                    option.textContent = providerNames[provider] || provider;
                    if (provider === data.default) {
                        option.selected = true;
                    }
                    select.appendChild(option);
                });
            }
        });

        if (availableProviders.length > 0) {
            addMessage('system', `✅ Proveedores disponibles: ${availableProviders.map(p => providerNames[p]).join(', ')}`);
        }

    } catch (error) {
        console.error('Error loading providers:', error);
        addMessage('system', '⚠️ No se pudieron cargar los proveedores de IA');
    }
}

// ============================================
// EXPLORADOR DE ARCHIVOS
// ============================================
async function refreshFiles(path = '') {
    try {
        updateStatus('Cargando archivos...');
        const response = await fetch(`/api/files?path=${encodeURIComponent(path)}`);
        const data = await response.json();
        renderFileTree(data);
        updateStatus('Listo');
    } catch (error) {
        console.error('Error:', error);
        updateStatus('❌ Error al cargar archivos');
    }
}

function renderFileTree(data) {
    const tree = document.getElementById('fileTree');
    const pathDiv = document.getElementById('currentPath');

    if (!tree) return;

    pathDiv.textContent = data.current_path || 'Raíz';
    tree.innerHTML = '';

    if (data.current_path) {
        const upBtn = document.createElement('div');
        upBtn.className = 'folder';
        upBtn.textContent = '📁 .. (Subir)';
        upBtn.onclick = () => {
            const parent = data.current_path.split('/').slice(0, -1).join('/');
            refreshFiles(parent);
        };
        tree.appendChild(upBtn);
    }

    data.folders.forEach(folder => {
        const div = document.createElement('div');
        div.className = 'folder';
        div.textContent = `📁 ${folder.name}`;
        div.onclick = () => refreshFiles(folder.path);
        tree.appendChild(div);
    });

    data.files.forEach(file => {
        const div = document.createElement('div');
        div.className = 'file';
        div.textContent = `📄 ${file.name}`;
        div.onclick = () => selectFile(file);
        tree.appendChild(div);
    });

    if (data.folders.length === 0 && data.files.length === 0) {
        tree.innerHTML = '<p style="padding: 20px; text-align: center; color: #999;">Carpeta vacía</p>';
    }
}

function selectFile(file) {
    currentFile = file;
    document.querySelectorAll('.file').forEach(el => el.classList.remove('selected'));
    event.target.classList.add('selected');
    loadPDF(file.path);
    updateStatus(`Archivo: ${file.name}`);
}

function loadPDF(path) {
    const viewer = document.getElementById('pdfViewer');
    const btnOCR = document.getElementById('btnOCR');
    viewer.innerHTML = `<iframe src="/api/pdf/${encodeURIComponent(path)}"></iframe>`;
    btnOCR.disabled = false;
    ocrText = '';
}

// ============================================
// OCR
// ============================================
async function runOCR() {
    if (!currentFile) return;

    try {
        updateStatus('🔍 Ejecutando OCR...');
        const btnOCR = document.getElementById('btnOCR');
        btnOCR.disabled = true;
        btnOCR.innerHTML = '<span class="loading"></span> Procesando...';

        const response = await fetch('/api/ocr', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ filename: currentFile.path })
        });

        const data = await response.json();

        if (data.text) {
            ocrText = data.text;
            addMessage('system', `✅ OCR completado: ${data.text.length} caracteres extraídos`);
            addMessage('assistant', `He procesado "${currentFile.name}". Puedes hacerme preguntas sobre el contenido.`);
            updateStatus('✅ OCR completado');
        } else {
            addMessage('system', '⚠️ No se pudo extraer texto del documento');
            updateStatus('⚠️ OCR sin resultados');
        }

    } catch (error) {
        console.error('Error:', error);
        addMessage('system', '❌ Error al ejecutar OCR');
        updateStatus('❌ Error en OCR');
    } finally {
        const btnOCR = document.getElementById('btnOCR');
        btnOCR.disabled = false;
        btnOCR.textContent = '🔍 Ejecutar OCR';
    }
}

// ============================================
// CHAT CON IA
// ============================================
async function sendMessage() {
    const promptInput = document.getElementById('chatPrompt');
    const prompt = promptInput.value.trim();

    if (!prompt) return;

    const provider = document.getElementById('aiProvider').value;
    const mode = document.getElementById('aiMode').value;

    addMessage('user', prompt);
    promptInput.value = '';

    const modeNames = {
        'standard': '⚡ Rápida',
        'deep': '🔍 Profunda',
        'research': '📚 Investigación'
    };

    const loadingId = addMessage('assistant', `<span class="loading"></span> ${modeNames[mode]} con ${provider}...`);
    updateStatus(`💬 Consultando ${provider} (${modeNames[mode]})...`);

    try {
        const response = await fetch('/api/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                prompt: prompt,
                context: ocrText,
                provider: provider,
                mode: mode
            })
        });

        const data = await response.json();

        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) {
            if (data.success) {
                loadingMsg.innerHTML = data.response;
            } else {
                loadingMsg.innerHTML = `❌ Error: ${data.error}`;
                loadingMsg.classList.add('error');
            }
        }

        updateStatus('Listo');

    } catch (error) {
        console.error('Error:', error);
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) {
            loadingMsg.textContent = '❌ Error al conectar con IA';
        }
        updateStatus('❌ Error en chat');
    }
}

function addMessage(type, text) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const msgId = 'msg-' + Date.now();

    const div = document.createElement('div');
    div.id = msgId;
    div.className = `message ${type}`;
    div.innerHTML = text;

    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    return msgId;
}

// ============================================
// GENERADOR DE DOCUMENTOS
// ============================================
async function loadDocumentTemplates() {
    try {
        const response = await fetch('/api/documents/templates');
        const templates = await response.json();

        const container = document.getElementById('docTypes');
        if (!container) return;

        container.innerHTML = '';

        Object.entries(templates).forEach(([type, template]) => {
            const btn = document.createElement('button');
            btn.className = 'doc-type-btn';
            btn.onclick = () => selectDocType(type, template);
            btn.innerHTML = `
                <strong>${template.name}</strong>
                <small>${template.description}</small>
            `;
            container.appendChild(btn);
        });

    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

function selectDocType(type, template) {
    currentDocType = type;

    document.querySelectorAll('.doc-type-btn').forEach(btn => btn.classList.remove('active'));
    event.target.classList.add('active');

    document.getElementById('docFormTitle').textContent = template.name;
    document.getElementById('docFormDesc').textContent = template.description;
    document.getElementById('documentForm').classList.remove('hidden');
    document.getElementById('generatedDoc').classList.add('hidden');

    const fieldsContainer = document.getElementById('formFields');
    fieldsContainer.innerHTML = '';

    template.fields.forEach(field => {
        const group = document.createElement('div');
        group.className = 'form-group';

        const label = document.createElement('label');
        label.textContent = field.label;
        group.appendChild(label);

        let input;
        if (field.type === 'textarea') {
            input = document.createElement('textarea');
            input.rows = 4;
        } else if (field.type === 'select') {
            input = document.createElement('select');
            field.options.forEach(opt => {
                const option = document.createElement('option');
                option.value = opt;
                option.textContent = opt;
                input.appendChild(option);
            });
        } else {
            input = document.createElement('input');
            input.type = field.type;
        }

        input.name = field.name;
        input.id = `field-${field.name}`;
        group.appendChild(input);

        fieldsContainer.appendChild(group);
    });
}

async function generateDocument() {
    if (!currentDocType) {
        console.warn('No hay tipo de documento seleccionado');
        return;
    }

    const formData = {};
    let valid = true;

    document
        .querySelectorAll('#formFields input[required], #formFields textarea[required]')
        .forEach(field => {
            if (!field.value.trim()) {
                field.classList.add('error-field');
                valid = false;
            } else {
                field.classList.remove('error-field');
                formData[field.name] = field.value;
            }
        });

    if (!valid) {
        if (typeof showValidationError === 'function') {
            showValidationError('Completa todos los campos obligatorios antes de generar el documento.');
        }
        return;
    }

    const provider = document.getElementById('docProvider').value;
    const btn = document.querySelector('.btn-generate');

    if (btn) {
        btn.disabled = true;
        btn.textContent = '⏳ Generando...';
    }

    updateStatus('✨ Generando documento con IA...');

    try {
        const response = await fetch('/api/documents/generate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                type: currentDocType,
                data: formData,
                provider: provider
            })
        });

        const result = await response.json();

        if (result.success) {
            document.getElementById('docContent').textContent = result.content;
            document.getElementById('documentForm').classList.add('hidden');
            document.getElementById('generatedDoc').classList.remove('hidden');
            updateStatus(`✅ Documento generado: ${result.filename}`);
        } else {
            const msg = `Error al generar documento: ${result.error}`;
            if (typeof showValidationError === 'function') {
                showValidationError(msg);
            } else {
                alert(msg);
            }
            updateStatus('❌ Error al generar documento');
        }
    } catch (error) {
        console.error('Error:', error);
        if (typeof showValidationError === 'function') {
            showValidationError('Error de conexión al generar el documento.');
        } else {
            alert('Error de conexión al generar el documento.');
        }
        updateStatus('❌ Error en generación');
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.textContent = '✨ Generar Documento';
        }
    }
}

function copyDocument() {
    const content = document.getElementById('docContent').textContent;
    navigator.clipboard.writeText(content).then(() => {
        updateStatus('✅ Documento copiado al portapapeles');
    });
}

function downloadDocument() {
    const content = document.getElementById('docContent').textContent;
    const blob = new Blob([content], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${currentDocType}_${new Date().getTime()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    updateStatus('✅ Documento descargado');
}

function resetGenerator() {
    document.getElementById('documentForm').classList.remove('hidden');
    document.getElementById('generatedDoc').classList.add('hidden');
    document.getElementById('formFields').querySelectorAll('input, textarea').forEach(field => {
        field.value = '';
    });
    updateStatus('Listo para nuevo documento');
}

// ============================================
// ANALIZADOR LEXNET
// ============================================
function initializeLexNetUploader() {
    const uploadZone = document.getElementById('uploadZone');

    if (uploadZone) {
        uploadZone.addEventListener('click', () => {
            document.getElementById('fileMultiple').click();
        });

        uploadZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadZone.classList.add('dragover');
        });

        uploadZone.addEventListener('dragleave', () => {
            uploadZone.classList.remove('dragover');
        });

        uploadZone.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadZone.classList.remove('dragover');

            const files = Array.from(e.dataTransfer.files);
            addFiles(files);
        });
    }
}

function handleMultipleFiles() {
    const fileInput = document.getElementById('fileMultiple');
    const files = Array.from(fileInput.files);
    addFiles(files);
}

function addFiles(files) {
    files.forEach(file => {
        if (!uploadedFiles.find(f => f.name === file.name && f.size === file.size)) {
            uploadedFiles.push(file);
            addFileToList(file);
        }
    });

    updateAnalyzeButton();
    classifyFiles();
}

function addFileToList(file) {
    const filesList = document.getElementById('filesList');
    if (!filesList) return;

    const fileItem = document.createElement('div');
    fileItem.className = 'file-item';
    fileItem.id = `file-${uploadedFiles.length - 1}`;

    const icon = getFileIcon(file.name);
    const size = formatFileSize(file.size);

    fileItem.innerHTML = `
        <div class="file-info">
            <span class="file-icon">${icon}</span>
            <div class="file-details">
                <span class="file-name">${file.name}</span>
                <span class="file-meta">${size} • ${file.type || 'Desconocido'}</span>
            </div>
        </div>
        <div class="file-status" id="status-${uploadedFiles.length - 1}">
            ⏳ Pendiente
        </div>
        <button class="file-remove" onclick="removeFile(${uploadedFiles.length - 1})">
            🗑️ Quitar
        </button>
    `;

    filesList.appendChild(fileItem);
}

function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    const icons = {
        'pdf': '📄', 'jpg': '🖼️', 'jpeg': '🖼️', 'png': '🖼️',
        'doc': '📝', 'docx': '📝', 'xls': '📊', 'xlsx': '📊'
    };
    return icons[ext] || '📎';
}

function formatFileSize(bytes) {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
}

function removeFile(index) {
    uploadedFiles.splice(index, 1);
    const filesList = document.getElementById('filesList');
    filesList.innerHTML = '';
    uploadedFiles.forEach(addFileToList);
    updateAnalyzeButton();
}

function updateAnalyzeButton() {
    const btnAnalyze = document.getElementById('btnAnalyze');
    if (btnAnalyze) {
        btnAnalyze.disabled = uploadedFiles.length === 0;
    }
}

function classifyFiles() {
    // Implementación simplificada
    updateStatus(`${uploadedFiles.length} archivo(s) cargado(s)`);
}

// Placeholder functions
function analyzeLexNetFlexible() {
    alert('Función en desarrollo');
}

function copyLexNetAnalysis() { }
function downloadLexNetAnalysis() { }
function exportToiCloud() { }
function resetLexNet() {
    uploadedFiles = [];
    document.getElementById('filesList').innerHTML = '';
    updateAnalyzeButton();
}

// ============================================
// UTILIDADES
// ============================================
function updateStatus(text) {
    const status = document.getElementById('status');
    if (status) {
        status.textContent = text;
    }
}

// ============================================
// ANALIZADOR LEXNET - VERSIÓN SIMPLE
// ============================================
let lexnetFiles = {
    resumen: null,
    caratula: null,
    principal: null
};

let lexnetTexts = {
    resumen: '',
    caratula: '',
    principal: ''
};

function handleLexNetFile(type) {
    const fileInput = document.getElementById(`file${type.charAt(0).toUpperCase() + type.slice(1)}`);
    const statusSpan = document.getElementById(`status${type.charAt(0).toUpperCase() + type.slice(1)}`);

    const file = fileInput.files[0];
    if (file) {
        lexnetFiles[type] = file;
        statusSpan.textContent = file.name;
        statusSpan.classList.add('uploaded');

        updateStatus(`📄 ${file.name} cargado`);
        checkLexNetReady();
    }
}

function checkLexNetReady() {
    const btnAnalyze = document.getElementById('btnAnalyzeLexNet');

    // Requerir al menos resumen y principal
    if (lexnetFiles.resumen && lexnetFiles.principal) {
        btnAnalyze.disabled = false;
    } else {
        btnAnalyze.disabled = true;
    }
}

async function analyzeLexNet() {
    const provider = document.getElementById('lexnetProvider').value;
    const btnAnalyze = document.getElementById('btnAnalyzeLexNet');

    btnAnalyze.disabled = true;
    btnAnalyze.innerHTML = '<span class="loading"></span> Analizando...';

    updateStatus('🔍 Extrayendo texto con OCR...');

    try {
        // Extraer texto de cada PDF
        if (lexnetFiles.resumen) {
            updateStatus('📋 Procesando RESUMEN...');
            lexnetTexts.resumen = await extractTextFromUploadedFile(lexnetFiles.resumen);
        }

        if (lexnetFiles.caratula) {
            updateStatus('📄 Procesando CARATULA...');
            lexnetTexts.caratula = await extractTextFromUploadedFile(lexnetFiles.caratula);
        }

        if (lexnetFiles.principal) {
            updateStatus('⚖️ Procesando resolución principal...');
            lexnetTexts.principal = await extractTextFromUploadedFile(lexnetFiles.principal);
        }

        updateStatus('🤖 Analizando con IA...');

        // Enviar a analizar
        const response = await fetch('/api/lexnet/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                textos: lexnetTexts,
                provider: provider
            })
        });

        const result = await response.json();

        if (result.success) {
            currentAnalysis = result.analisis;

            // Mostrar análisis
            document.getElementById('lexnetContent').textContent = result.analisis;
            document.getElementById('lexnetActions').classList.remove('hidden');

            updateStatus(`✅ Análisis completado: ${result.filename}`);
        } else {
            alert(`Error: ${result.error}`);
            updateStatus('❌ Error en análisis');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Error al analizar la notificación');
        updateStatus('❌ Error en análisis');
    } finally {
        btnAnalyze.disabled = false;
        btnAnalyze.textContent = '🔍 Analizar Notificación';
    }
}

async function extractTextFromUploadedFile(file) {
    try {
        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/ocr/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        if (result.success) {
            return result.text;
        } else {
            throw new Error(result.error);
        }

    } catch (error) {
        console.error('Error extrayendo texto:', error);
        return '';
    }
}

function copyLexNetAnalysis() {
    navigator.clipboard.writeText(currentAnalysis).then(() => {
        updateStatus('✅ Análisis copiado al portapapeles');
    });
}

function downloadLexNetAnalysis() {
    const blob = new Blob([currentAnalysis], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `analisis_lexnet_${new Date().getTime()}.txt`;
    a.click();
    URL.revokeObjectURL(url);
    updateStatus('✅ Análisis descargado');
}

function resetLexNet() {
    // Reset files
    lexnetFiles = { resumen: null, caratula: null, principal: null };
    lexnetTexts = { resumen: '', caratula: '', principal: '' };
    currentAnalysis = '';

    // Reset UI
    document.getElementById('fileResumen').value = '';
    document.getElementById('fileCaratula').value = '';
    document.getElementById('filePrincipal').value = '';

    document.getElementById('statusResumen').textContent = 'Ningún archivo';
    document.getElementById('statusCaratula').textContent = 'Ningún archivo';
    document.getElementById('statusPrincipal').textContent = 'Ningún archivo';

    document.getElementById('statusResumen').classList.remove('uploaded');
    document.getElementById('statusCaratula').classList.remove('uploaded');
    document.getElementById('statusPrincipal').classList.remove('uploaded');

    document.getElementById('lexnetContent').innerHTML = '<p class="placeholder">Sube al menos RESUMEN.pdf y Resolución Principal, luego presiona "Analizar Notificación"</p>';
    document.getElementById('lexnetActions').classList.add('hidden');

    checkLexNetReady();
    updateStatus('Listo para nuevo análisis');
}

// ELIMINAR las funciones duplicadas/obsoletas
if (typeof initializeLexNetUploader !== 'undefined') {
    delete window.initializeLexNetUploader;
}
if (typeof handleMultipleFiles !== 'undefined') {
    delete window.handleMultipleFiles;
}
if (typeof addFiles !== 'undefined') {
    delete window.addFiles;
}
if (typeof addFileToList !== 'undefined') {
    delete window.addFileToList;
}
if (typeof removeFile !== 'undefined') {
    delete window.removeFile;
}
if (typeof classifyFiles !== 'undefined') {
    delete window.classifyFiles;
}
if (typeof analyzeLexNetFlexible !== 'undefined') {
    delete window.analyzeLexNetFlexible;
}
if (typeof exportToiCloud !== 'undefined') {
    delete window.exportToiCloud;
}
// ============================================
// ANALIZADOR LEXNET - VERSIÓN MÚLTIPLE SIMPLE
// ============================================
let lexnetMultipleFiles = [];

function handleMultipleFilesLexNet() {
    const fileInput = document.getElementById('filesMultiple');
    const files = Array.from(fileInput.files);

    // Añadir nuevos archivos
    files.forEach(file => {
        if (!lexnetMultipleFiles.find(f => f.name === file.name && f.size === file.size)) {
            lexnetMultipleFiles.push(file);
        }
    });

    renderFilesListLexNet();
    updateAnalyzeLexNetButton();
}

function renderFilesListLexNet() {
    const container = document.getElementById('filesListLexNet');
    container.innerHTML = '';

    if (lexnetMultipleFiles.length === 0) {
        return;
    }

    lexnetMultipleFiles.forEach((file, index) => {
        const item = document.createElement('div');
        item.className = 'file-item-simple';

        const icon = getFileIcon(file.name);

        item.innerHTML = `
            <span>${icon} <span class="file-name-simple">${file.name}</span></span>
            <button class="file-remove-simple" onclick="removeFileLexNet(${index})">Quitar</button>
        `;

        container.appendChild(item);
    });

    updateStatus(`${lexnetMultipleFiles.length} archivo(s) listo(s) para analizar`);
}

function removeFileLexNet(index) {
    lexnetMultipleFiles.splice(index, 1);
    renderFilesListLexNet();
    updateAnalyzeLexNetButton();
}

function updateAnalyzeLexNetButton() {
    const btn = document.getElementById('btnAnalyzeLexNet');
    btn.disabled = lexnetMultipleFiles.length === 0;
}

async function analyzeLexNetMultiple() {
    const provider = document.getElementById('lexnetProvider').value;
    const btn = document.getElementById('btnAnalyzeLexNet');

    btn.disabled = true;
    btn.innerHTML = '<span class="loading"></span> Analizando...';

    try {
        // Procesar todos los archivos
        const textos = {};

        for (let i = 0; i < lexnetMultipleFiles.length; i++) {
            const file = lexnetMultipleFiles[i];
            updateStatus(`📄 Procesando ${i + 1}/${lexnetMultipleFiles.length}: ${file.name}...`);

            const text = await extractTextFromUploadedFile(file);

            // Clasificar automáticamente
            const name = file.name.toLowerCase();
            if (name.includes('resumen') || name.includes('acuse')) {
                textos.resumen = text;
            } else if (name.includes('caratula') || name.includes('carátula')) {
                textos.caratula = text;
            } else if (!textos.principal) {
                // El primero que no sea resumen/caratula es el principal
                textos.principal = text;
            } else {
                // Adjuntos
                if (!textos.adjuntos) textos.adjuntos = [];
                textos.adjuntos.push(text);
            }
        }

        // Si no hay principal, usar el primer archivo
        if (!textos.principal && lexnetMultipleFiles.length > 0) {
            textos.principal = await extractTextFromUploadedFile(lexnetMultipleFiles[0]);
        }

        updateStatus('🤖 Analizando con IA...');

        // Enviar a analizar
        const response = await fetch('/api/lexnet/analyze', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                textos: textos,
                provider: provider,
                archivos: lexnetMultipleFiles.map(f => ({ nombre: f.name }))
            })
        });

        const result = await response.json();

        if (result.success) {
            currentAnalysis = result.analisis;
            document.getElementById('lexnetContent').textContent = result.analisis;
            document.getElementById('lexnetActions').classList.remove('hidden');
            updateStatus(`✅ Análisis completado`);
        } else {
            alert(`Error: ${result.error}`);
            updateStatus('❌ Error en análisis');
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Error al analizar: ' + error.message);
        updateStatus('❌ Error');
    } finally {
        btn.disabled = false;
        btn.textContent = '🔍 Analizar Notificación';
    }
}

function resetLexNetMultiple() {
    lexnetMultipleFiles = [];
    document.getElementById('filesMultiple').value = '';
    document.getElementById('filesListLexNet').innerHTML = '';
    document.getElementById('lexnetContent').innerHTML = '<p class="placeholder">Sube al menos 1 documento y presiona "Analizar Notificación"</p>';
    document.getElementById('lexnetActions').classList.add('hidden');
    updateAnalyzeLexNetButton();
    updateStatus('Listo para nuevo análisis');
}

// Limpiar funciones antiguas de LexNet
const oldLexnetFunctions = [
    'handleLexNetFile',
    'checkLexNetReady',
    'analyzeLexNet',
    'resetLexNet'
];

oldLexnetFunctions.forEach(fname => {
    if (typeof window[fname] !== 'undefined') {
        delete window[fname];
    }
});

// Mejorar extractTextFromUploadedFile con más logging
async function extractTextFromUploadedFile(file) {
    try {
        console.log(`📄 Extrayendo texto de: ${file.name} (${file.size} bytes)`);

        const formData = new FormData();
        formData.append('file', file);

        const response = await fetch('/api/ocr/upload', {
            method: 'POST',
            body: formData
        });

        const result = await response.json();

        console.log('OCR resultado:', result);

        if (result.success) {
            console.log(`✅ Texto extraído: ${result.text.length} caracteres`);
            return result.text;
        } else {
            console.error('❌ Error OCR:', result.error);
            throw new Error(result.error);
        }

    } catch (error) {
        console.error('❌ Error extrayendo texto:', error);
        return `[Error procesando ${file.name}: ${error.message}]`;
    }
}

// ============================================================================
// GENERADOR DE DOCUMENTOS (añadido 31/01/2026)
// ============================================================================

const DOCUMENT_TYPES = {
    demanda_civil: {
        name: 'Demanda Civil',
        icon: '⚖️',
        desc: 'Demanda completa para juicio ordinario o verbal',
        fields: [
            { name: 'juzgado', label: 'Juzgado', type: 'text', placeholder: 'Juzgado de Primera Instancia nº...' },
            { name: 'demandante', label: 'Demandante', type: 'text', placeholder: 'Nombre completo' },
            { name: 'demandado', label: 'Demandado', type: 'text', placeholder: 'Nombre completo' },
            { name: 'hechos', label: 'Hechos', type: 'textarea', placeholder: 'Narración de los hechos...' },
            { name: 'petitorio', label: 'Petitorio', type: 'textarea', placeholder: 'Se solicita que...' }
        ]
    },
    contestacion_demanda: {
        name: 'Contestación a la Demanda',
        icon: '🛡️',
        desc: 'Respuesta formal a demanda civil',
        fields: [
            { name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento ordinario nº...' },
            { name: 'demandado', label: 'Demandado (quien contesta)', type: 'text', placeholder: 'Nombre completo' },
            { name: 'hechos_propios', label: 'Hechos propios', type: 'textarea', placeholder: 'Versión de los hechos...' },
            { name: 'excepciones', label: 'Excepciones y defensas', type: 'textarea', placeholder: 'Defensas jurídicas...' },
            { name: 'suplica', label: 'Súplica', type: 'textarea', placeholder: 'Se solicita la desestimación...' }
        ]
    },
    recurso_apelacion: {
        name: 'Recurso de Apelación',
        icon: '🔄',
        desc: 'Recurso contra sentencia de primera instancia',
        fields: [
            { name: 'sentencia', label: 'Sentencia a recurrir', type: 'text', placeholder: 'Sentencia nº... de fecha...' },
            { name: 'recurrente', label: 'Recurrente', type: 'text', placeholder: 'Nombre completo' },
            { name: 'fundamentos', label: 'Fundamentos de Derecho', type: 'textarea', placeholder: 'Infracciones cometidas...' },
            { name: 'suplica', label: 'Súplica', type: 'textarea', placeholder: 'Se suplica la revocación...' }
        ]
    },
    recurso_reposicion: {
        name: 'Recurso de Reposición',
        icon: '🔁',
        desc: 'Recurso contra autos y providencias',
        fields: [
            { name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...' },
            { name: 'resolucion', label: 'Resolución recurrida', type: 'text', placeholder: 'Auto/Providencia de fecha...' },
            { name: 'recurrente', label: 'Recurrente', type: 'text', placeholder: 'Nombre completo' },
            { name: 'motivos', label: 'Motivos del recurso', type: 'textarea', placeholder: 'Fundamentos del recurso...' }
        ]
    },
    escrito_alegaciones: {
        name: 'Escrito de Alegaciones',
        icon: '📝',
        desc: 'Respuesta a trámite de alegaciones',
        fields: [
            { name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...' },
            { name: 'parte', label: 'En nombre de', type: 'text', placeholder: 'Nombre de la parte' },
            { name: 'alegaciones', label: 'Alegaciones', type: 'textarea', placeholder: 'Contenido de las alegaciones...' }
        ]
    },
    desistimiento: {
        name: 'Desistimiento',
        icon: '🚫',
        desc: 'Escrito de desistimiento del procedimiento',
        fields: [
            { name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...' },
            { name: 'parte', label: 'Parte que desiste', type: 'text', placeholder: 'Nombre completo' },
            { name: 'motivo', label: 'Motivo (opcional)', type: 'textarea', placeholder: 'Por convenir a mis intereses...' }
        ]
    },
    personacion: {
        name: 'Personación y Solicitud de Copias',
        icon: '👤',
        desc: 'Primera comparecencia en autos',
        fields: [
            { name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...' },
            { name: 'parte', label: 'En nombre de', type: 'text', placeholder: 'Nombre del representado' },
            { name: 'procurador', label: 'Procurador', type: 'text', placeholder: 'Nombre del procurador' },
            { name: 'abogado', label: 'Abogado', type: 'text', placeholder: 'Nombre del abogado' }
        ]
    },
    poder_procesal: {
        name: 'Poder para Pleitos',
        icon: '📜',
        desc: 'Otorgamiento de poder procesal',
        fields: [
            { name: 'poderdante', label: 'Poderdante', type: 'text', placeholder: 'Nombre completo' },
            { name: 'apoderado', label: 'Apoderado (Procurador)', type: 'text', placeholder: 'Nombre del procurador' },
            { name: 'dni_poderdante', label: 'DNI Poderdante', type: 'text', placeholder: '12345678A' },
            { name: 'ambito', label: 'Ámbito del poder', type: 'text', placeholder: 'General o específico' }
        ]
    },
    escrito_prueba: {
        name: 'Proposición de Prueba',
        icon: '🔬',
        desc: 'Escrito de proposición de medios de prueba',
        fields: [
            { name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...' },
            { name: 'parte', label: 'Parte que propone', type: 'text', placeholder: 'Nombre de la parte' },
            { name: 'hechos', label: 'Hechos a probar', type: 'textarea', placeholder: 'Hechos controvertidos...' },
            { name: 'pruebas', label: 'Medios de prueba', type: 'textarea', placeholder: 'Documental, testifical, pericial...' }
        ]
    },
    burofax: {
        name: 'Burofax',
        icon: '📮',
        desc: 'Comunicación fehaciente por burofax',
        fields: [
            { name: 'remitente', label: 'Remitente', type: 'text', placeholder: 'Nombre y dirección completa' },
            { name: 'destinatario', label: 'Destinatario', type: 'text', placeholder: 'Nombre y dirección completa' },
            { name: 'asunto', label: 'Asunto', type: 'text', placeholder: 'Resumen del asunto' },
            { name: 'contenido', label: 'Contenido', type: 'textarea', placeholder: 'Texto del burofax...' }
        ]
    },
    requerimiento: {
        name: 'Requerimiento Extrajudicial',
        icon: '⚠️',
        desc: 'Requerimiento previo a reclamación judicial',
        fields: [
            { name: 'requirente', label: 'Requirente', type: 'text', placeholder: 'Quien requiere' },
            { name: 'requerido', label: 'Requerido', type: 'text', placeholder: 'Destinatario' },
            { name: 'objeto', label: 'Objeto del requerimiento', type: 'textarea', placeholder: 'Contenido del requerimiento...' },
            { name: 'plazo', label: 'Plazo', type: 'text', placeholder: 'Ej: 10 días hábiles' }
        ]
    },
    querella: {
        name: 'Querella Criminal',
        icon: '⚔️',
        desc: 'Escrito de querella penal',
        fields: [
            { name: 'querellante', label: 'Querellante', type: 'text', placeholder: 'Nombre completo' },
            { name: 'querellado', label: 'Querellado', type: 'text', placeholder: 'Nombre completo' },
            { name: 'hechos', label: 'Hechos denunciados', type: 'textarea', placeholder: 'Narración cronológica...' },
            { name: 'delito', label: 'Delito/s', type: 'text', placeholder: 'Ej: Estafa (art. 248 CP)' },
            { name: 'pruebas', label: 'Pruebas', type: 'textarea', placeholder: 'Medios probatorios...' }
        ]
    }
};


function initDocumentGenerator() {
    console.log('🔧 Inicializando generador de documentos...');
    renderDocumentTypes();
}

function renderDocumentTypes() {
    const container = document.getElementById('docTypes');
    if (!container) return;

    let html = '';
    for (const [key, doc] of Object.entries(DOCUMENT_TYPES)) {
        html += `
            <div class="doc-type" onclick="selectDocumentType('${key}')">
                <span class="doc-type-icon">${doc.icon}</span>
                <span class="doc-type-name">${doc.name}</span>
            </div>
        `;
    }
    container.innerHTML = html;
}

function selectDocumentType(type) {
    currentDocType = type;
    const doc = DOCUMENT_TYPES[type];

    // Actualizar título y descripción
    document.getElementById('docFormTitle').textContent = `${doc.icon} ${doc.name}`;
    document.getElementById('docFormDesc').textContent = doc.desc;

    // Generar campos del formulario
    let fieldsHtml = '';
    doc.fields.forEach(field => {
        if (field.type === 'textarea') {
            fieldsHtml += `
                <div class="form-group">
                    <label>${field.label}</label>
                    <textarea 
                        name="${field.name}" 
                        placeholder="${field.placeholder}"
                        rows="4"
                        required
                    ></textarea>
                </div>
            `;
        } else {
            fieldsHtml += `
                <div class="form-group">
                    <label>${field.label}</label>
                    <input 
                        type="${field.type}" 
                        name="${field.name}" 
                        placeholder="${field.placeholder}"
                        required
                    />
                </div>
            `;
        }
    });

    document.getElementById('formFields').innerHTML = fieldsHtml;
    document.getElementById('documentForm').classList.remove('hidden');
    document.getElementById('generatedDoc').classList.add('hidden');

    // Marcar tipo seleccionado
    document.querySelectorAll('.doc-type').forEach(el => el.classList.remove('active'));
    event.target.closest('.doc-type').classList.add('active');
}

function resetGenerator() {
    currentDocType = null;
    generatedContent = null;
    generatedFilename = null;

    document.getElementById('documentForm').reset();
    document.getElementById('documentForm').classList.add('hidden');
    document.getElementById('generatedDoc').classList.add('hidden');
    document.getElementById('docFormTitle').textContent = 'Selecciona un tipo de documento';
    document.getElementById('docFormDesc').textContent = '';

    document.querySelectorAll('.doc-type').forEach(el => el.classList.remove('active'));

    updateStatus('Listo');
}

// Auto-inicializar cuando se carga la página
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initDocumentGenerator);
} else {
    initDocumentGenerator();
}


// ============================================
// EXPORTACIÓN A iCLOUD
// ============================================

async function checkiCloudStatus() {
    try {
        const response = await fetch('/api/icloud/status');
        const status = await response.json();

        if (status.available) {
            console.log('✅ iCloud Drive disponible');
            return true;
        } else {
            console.log('⚠️ iCloud Drive no disponible');
            return false;
        }
    } catch (error) {
        console.error('Error checking iCloud:', error);
        return false;
    }
}

async function exportDocumentToiCloud(content, filename, year, clientName, subfolder) {
    try {
        const response = await fetch('/api/icloud/export', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: content,
                filename: filename,
                year: year,
                client_name: clientName,
                subfolder: subfolder
            })
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ Exportado a iCloud:\n${result.filepath}`);
            updateStatus(`✅ Exportado a iCloud`);
        } else {
            alert(`❌ Error: ${result.error}`);
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Error al exportar a iCloud');
    }
}

async function exportAnalysisToClient() {
    const clientName = prompt('Nombre del cliente:');

    if (!clientName) {
        return;
    }

    try {
        const response = await fetch('/api/icloud/export-analysis', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                content: currentAnalysis,
                client_name: clientName
            })
        });

        const result = await response.json();

        if (result.success) {
            alert(`✅ Análisis exportado a iCloud para ${clientName}:\n${result.filepath}`);
        } else {
            alert(`❌ Error: ${result.error}`);
        }

    } catch (error) {
        console.error('Error:', error);
        alert('Error al exportar análisis');
    }
}

async function getiCloudClients() {
    try {
        const response = await fetch('/api/icloud/clients');
        const result = await response.json();

        if (result.success) {
            return result.clients;
        }
        return [];

    } catch (error) {
        console.error('Error:', error);
        return [];
    }
}

// Actualizar función exportToiCloud existente
function exportToiCloud() {
    exportAnalysisToClient();
}

// Botón de exportación para documentos generados
async function exportGeneratedDocToiCloud() {
    const clients = await getiCloudClients();

    let clientName;

    if (clients.length > 0) {
        const clientList = clients.join('\n');
        clientName = prompt(`Clientes existentes:\n${clientList}\n\nNombre del cliente (nuevo o existente):`);
    } else {
        clientName = prompt('Nombre del cliente:');
    }

    if (!clientName) return;

    const timestamp = new Date().getTime();
    const filename = `${currentDocType}_${timestamp}.txt`;

    await exportDocumentToiCloud(
        generatedDocContent,
        filename,
        new Date().getFullYear(),
        clientName,
        'GENERADOS'
    );
}

// ============================================
// CONSULTAS RÁPIDAS PREDEFINIDAS
// ============================================

function cargarConsulta(texto) {
    const textarea = document.getElementById('chatPrompt');
    if (textarea) {
        textarea.value = texto;
        textarea.focus();

        // Efecto visual
        textarea.style.background = '#e3f2fd';
        textarea.style.transition = 'background 0.3s ease';
        setTimeout(() => {
            textarea.style.background = '';
        }, 1000);

        // Scroll al textarea
        textarea.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        console.error('❌ No se encontró el textarea de chat');
    }
}

// Lista de consultas disponibles
const consultasPredefinidas = [
    {
        titulo: "📋 Elementos delito estafa",
        prompt: "Explica los elementos del delito de estafa según el Código Penal español",
        categoria: "penal"
    },
    {
        titulo: "⏰ Plazos procesales",
        prompt: "¿Cuáles son los plazos para recurrir una sentencia civil en España?",
        categoria: "civil"
    },
    {
        titulo: "📄 Requisitos demanda",
        prompt: "¿Qué requisitos formales debe cumplir una demanda civil según la LEC?",
        categoria: "civil"
    },
    {
        titulo: "🔍 Análisis Auto LexNET",
        prompt: "Analiza este auto judicial y extrae: tipo, fecha, tribunal, partes y decisión",
        categoria: "lexnet"
    }
];

console.log('✅ Sistema de consultas rápidas cargado:', consultasPredefinidas.length, 'consultas disponibles');

// ============================================
// VALIDACIÓN MEJORADA - GENERADOR DOCUMENTOS
// ============================================

function showValidationError(message) {
    let errorDiv = document.getElementById('validationError');
    if (!errorDiv) {
        errorDiv = document.createElement('div');
        errorDiv.id = 'validationError';
        errorDiv.className = 'validation-error';
        const formActions = document.querySelector('.form-actions');
        if (formActions) {
            formActions.parentNode.insertBefore(errorDiv, formActions);
        }
    }

    errorDiv.innerHTML = `
        <div class="error-content">
            <span class="error-icon">⚠️</span>
            <span class="error-message">${message}</span>
        </div>
    `;
    errorDiv.style.display = 'block';

    setTimeout(() => {
        errorDiv.style.display = 'none';
    }, 5000);
}


// ============================================
// AUTO-PROCESADOR FUNCTIONS
// ============================================

let currentDocumentId = null;
let autoProcesadorData = { stats: {}, documents: [], clientes: [] };

// Hook en switchTab EXISTENTE sin modificarlo
(function () {
    const originalSwitchTab = window.switchTab;
    if (typeof originalSwitchTab === 'function') {
        window.switchTab = function (tabName) {
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
            headers: { 'Content-Type': 'application/json' },
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
            headers: { 'Content-Type': 'application/json' },
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

// ====================
// FIX v2.3.1 - 04/02/2026
// ====================

document.addEventListener('DOMContentLoaded', function() {
    console.log('🔧 JS Dashboard Fixes cargados');
    
    // Fix Export PDF
    document.querySelectorAll('button, a').forEach(btn => {
        if (btn.textContent.includes('Exportar') || btn.textContent.includes('PDF')) {
            btn.onclick = function(e) {
                e.preventDefault();
                window.open('/api/dashboard/export-pdf', '_blank');
                console.log('📄 PDF export lanzado');
                return false;
            };
        }
    });
    
    // Fix Admin dropdown
    document.querySelectorAll('button, a').forEach(btn => {
        if (btn.textContent.includes('Admin') || btn.textContent.includes('admin')) {
            btn.onclick = function(e) {
                e.preventDefault();
                window.location.href = '/#admin';
                console.log('👤 Admin abierto');
                return false;
            };
        }
    });
    
    // Limpiar "En Revisión" si está vacío
    fetch('/api/dashboard/stats')
        .then(r => r.json())
        .then(stats => {
            if (stats.review === 0) {
                document.querySelectorAll('[data-status="revision"]').forEach(el => {
                    el.innerHTML = '0';
                });
            }
        })
        .catch(e => console.log('Stats fetch OK, ignorando:', e));
    
    console.log('✅ Todos fixes aplicados');
});
// SIDEBAR ENTERPRISE v3.0
document.addEventListener('DOMContentLoaded', () => {
    const sidebar = document.getElementById('sidebar');
    const toggle = document.getElementById('sidebar-toggle');
    const navItems = document.querySelectorAll('.nav-item');

    // Toggle Sidebar
    toggle.addEventListener('click', () => {
        sidebar.classList.toggle('open');
    });

    // Nav Items
    navItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            navItems.forEach(i => i.classList.remove('active'));
            item.classList.add('active');
            // Cargar contenido dinámico
            const tab = item.getAttribute('data-tab');
            loadTab(tab);
        });
    });

    // Auto-collapse mobile
    if (window.innerWidth < 768) {
        sidebar.classList.add('mobile');
    }
    window.addEventListener('resize', () => {
        if (window.innerWidth < 768) sidebar.classList.add('mobile');
        else sidebar.classList.remove('mobile');
    });
});

function loadTab(tab) {
    console.log(`Cargando tab: ${tab}`);
    // LexNET Urgente
    if (tab === 'lexnet') {
        fetch('/api/lexnet-urgent').then(r => r.json()).then(data => {
            document.querySelector('.urgent').textContent = data.count || 0;
        });
    }
    // Auto-Procesos Status
    if (tab === 'autoprocesos') {
        fetch('/api/watchdog-status').then(r => r.json()).then(status => {
            console.log('Watchdog:', status);
        });
    }
}

function initTrendChart(labels, values) {
    const ctx = document.getElementById('trendChart').getContext('2d');
    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Documentos Procesados',
                data: values,
                borderColor: '#007BFF',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                fill: True,
                tension: 0.4
            }]
        },
        options: { responsive: True, plugins: { legend: { display: False } } }
    });
}

// Cargar datos detallados al entrar al dashboard
async function refreshDashboard() {
    const r = await fetch('/api/dashboard/stats-detailed');
    const data = await r.json();
    if(data.success) {
        document.getElementById('kpi-today').innerText = data.kpis.today;
        document.getElementById('kpi-week').innerText = data.kpis.week;
        document.getElementById('kpi-month').innerText = data.kpis.month;
        
        initTrendChart(data.trends.labels, data.trends.values);
        
        const list = document.getElementById('recent-list');
        list.innerHTML = data.recent_docs.map(doc => `
            <div style='padding:10px; border-bottom:1px solid #eee; display:flex; justify-content:space-between;'>
                <span>📄 ${doc.name}</span>
                <small style='color:#888;'>${doc.time}</small>
            </div>
        `).join('');
    }
}
window.onload = refreshDashboard;

async function refreshLogs() {
    const section = document.getElementById('autoprocesos');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/autoprocesos/logs');
        const data = await r.json();
        const consoleDiv = document.getElementById('log-console');
        if (data.logs) {
            consoleDiv.innerHTML = data.logs.map(line => 
                `<div><span style='color:#569cd6;'>[${new Date().toLocaleTimeString()}]</span> ${line}</div>`
            ).join('');
            consoleDiv.scrollTop = consoleDiv.scrollHeight; // Auto-scroll al final
        }
    } catch(e) { console.error("Error cargando logs"); }
}

async function controlWatchdog(action) {
    const r = await fetch('/api/autoprocesos/toggle', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({action: action})
    });
    const data = await r.json();
    const label = document.getElementById('watchdog-status-label');
    if (data.status === 'running') {
        label.innerText = '● ACTIVO';
        label.style.color = 'green';
    } else {
        label.innerText = '● PAUSADO';
        label.style.color = '#ff4757';
    }
}

// Iniciar polling de logs
setInterval(refreshLogs, 5000);

async function enviarConsultaIA() {
    const input = document.getElementById('ia-prompt-input');
    const chatWindow = document.getElementById('ia-chat-window');
    const provider = document.getElementById('ia-provider-select').value;
    const prompt = input.value;

    if(!prompt) return;

    // Añadir mensaje del usuario
    chatWindow.innerHTML += `<div style='margin-bottom:15px; text-align:right;'><span style='background:#e3f2fd; padding:8px 12px; border-radius:15px; display:inline-block;'>${prompt}</span></div>`;
    input.value = '';
    chatWindow.scrollTop = chatWindow.scrollHeight;

    try {
        const r = await fetch('/api/ia/consultar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({prompt: prompt, provider: provider})
        });
        const data = await r.json();
        
        // Añadir respuesta de la IA
        chatWindow.innerHTML += `<div style='margin-bottom:15px;'><span style='background:#f1f1f1; padding:10px 15px; border-radius:15px; display:inline-block; border-left:4px solid var(--primary-blue);'><strong>${data.provider.toUpperCase()}:</strong><br>${data.respuesta}</span></div>`;
        chatWindow.scrollTop = chatWindow.scrollHeight;
    } catch(e) {
        chatWindow.innerHTML += `<div style='color:red;'>Error al conectar con el motor de IA</div>`;
    }
}

// Permitir enviar con Enter
document.getElementById('ia-prompt-input')?.addEventListener('keypress', (e) => {
    if (e.key === 'Enter') enviarConsultaIA();
});

async function loadPdfPreview() {
    const section = document.getElementById('pdf-preview');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/pdf/preview-data');
        const data = await r.json();
        
        if (data.success) {
            document.getElementById('pdf-current-name').innerText = data.filename;
            const container = document.getElementById('thumbs-container');
            
            container.innerHTML = data.thumbnails.map(thumb => `
                <div onclick='changePdfPage(${thumb.page})' style='cursor:pointer; margin-bottom:15px; text-align:center;'>
                    <img src='${thumb.url}' style='width:120px; border: 1px solid #ddd; border-radius:4px; transition:0.2s;' onmouseover='this.style.borderColor=\"#007BFF\"' onmouseout='this.style.borderColor=\"#ddd\"'>
                    <div style='font-size:0.75rem; color:#666; margin-top:4px;'>Pág. ${thumb.page}</div>
                </div>
            `).join('');
            
            // Cargar página 1 por defecto
            changePdfPage(1);
        }
    } catch(e) { console.error("Error cargando PDF Preview"); }
}

function changePdfPage(page) {
    const view = document.getElementById('active-page-view');
    view.innerHTML = `Página ${page} del Expediente`;
    view.style.color = "#333";
    console.log(`Cambiando a página ${page}`);
}

// Escuchar cambios de pestaña para cargar el PDF
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('PDF Preview')) setTimeout(loadPdfPreview, 100);
    });
});

async function saveAlertEmail() {
    const email = document.getElementById('alert-email-input').value;
    if(!email) return alert("Introduce un email válido");

    try {
        const r = await fetch('/api/alerts/config', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({email: email})
        });
        const data = await r.json();
        if(data.success) alert(data.message);
    } catch(e) { console.error("Error al guardar email"); }
}

async function loadAlertHistory() {
    const section = document.getElementById('email-alerts');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/alerts/history');
        const data = await r.json();
        const table = document.getElementById('alerts-history-table');
        
        table.innerHTML = data.history.map(item => `
            <tr style='border-bottom: 1px solid #eee;'>
                <td style='padding: 12px;'><span style='background: ${item.tipo === "CRÍTICA" ? "#f8d7da" : "#e2e3e5"}; color: ${item.tipo === "CRÍTICA" ? "#721c24" : "#383d41"}; padding: 4px 8px; border-radius: 4px; font-size: 0.75rem; font-weight: bold;'>${item.tipo}</span></td>
                <td style='padding: 12px;'>${item.asunto}</td>
                <td style='padding: 12px; color: #666; font-size: 0.85rem;'>${item.fecha}</td>
                <td style='padding: 12px; text-align: center; color: green;'>✅ ${item.estado}</td>
            </tr>
        `).join('');
    } catch(e) { console.error("Error al cargar historial"); }
}

// Cargar historial al entrar a la pestaña
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Email Alerts')) setTimeout(loadAlertHistory, 150);
    });
});

async function loadFirmaStatus() {
    const section = document.getElementById('firma-digital');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/firma/status');
        const data = await r.json();
        if(data.success) {
            document.getElementById('cert-name').innerText = `✅ ${data.ultimo_certificado} (Expira: ${data.expira})`;
        }
    } catch(e) { console.error("Error al cargar status de firma"); }
}

async function firmarDocumentoTest() {
    const btn = event.target;
    btn.innerText = "Firmando...";
    btn.disabled = true;

    try {
        const r = await fetch('/api/firma/ejecutar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({doc_id: "test-doc-123"})
        });
        const data = await r.json();
        
        if(data.success) {
            const resultDiv = document.getElementById('firma-result');
            resultDiv.style.display = 'block';
            resultDiv.innerHTML = `<strong>${data.message}</strong><br><small>Hash: ${data.hash}</small><br><small>Timestamp: ${data.timestamp}</small>`;
            btn.innerText = "FIRMAr OTRO";
            btn.disabled = false;
        }
    } catch(e) { alert("Error en el proceso de firma"); }
}

// Cargar status al entrar a la pestaña
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Firma Digital')) setTimeout(loadFirmaStatus, 150);
    });
});

async function loadBankingData() {
    const section = document.getElementById('banking');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r1 = await fetch('/api/banking/institutions');
        const d1 = await r1.json();
        const grid = document.getElementById('banking-grid');
        grid.innerHTML = d1.banks.map(bank => `
            <div style='background: white; border: 1px solid #eee; padding: 15px; border-radius: 8px; text-align: center; box-shadow: 0 2px 5px rgba(0,0,0,0.02);'>
                <div style='font-weight: bold; margin-bottom: 5px;'>${bank.name}</div>
                <div style='font-size: 0.8rem; color: ${bank.status === "Sincronizado" ? "green" : "#888"};'>● ${bank.status}</div>
                <div style='font-size: 1.1rem; font-weight: bold; margin-top: 10px;'>${bank.balance}</div>
            </div>
        `).join('');

        const r2 = await fetch('/api/banking/transactions');
        const d2 = await r2.json();
        const table = document.getElementById('banking-transactions-table');
        table.innerHTML = d2.transactions.map(t => `
            <tr style='border-bottom: 1px solid #eee;'>
                <td style='padding: 12px; font-size: 0.9rem;'>${t.date}</td>
                <td style='padding: 12px; font-size: 0.8rem; color: #666;'>${t.bank}</td>
                <td style='padding: 12px;'>${t.concept}</td>
                <td style='padding: 12px; text-align: right; font-weight: bold; color: ${t.amount > 0 ? "green" : "red"};'>${t.amount.toFixed(2)}€</td>
            </tr>
        `).join('');
    } catch(e) { console.error("Error al cargar datos bancarios"); }
}

// Cargar banking al entrar a la pestaña
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Banking')) setTimeout(loadBankingData, 150);
    });
});

async function loadEquipoDespacho() {
    const section = document.getElementById('usuarios');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/usuarios/equipo');
        const data = await r.json();
        const container = document.getElementById('equipo-list');
        
        container.innerHTML = data.usuarios.map(user => `
            <div style='display: flex; align-items: center; background: #f8f9fa; padding: 15px; border-radius: 8px; border: 1px solid #eee;'>
                <div style='width: 45px; height: 45px; background: #ddd; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 15px;'>${user.nombre.charAt(0)}</div>
                <div style='flex-grow: 1;'>
                    <div style='font-weight: bold;'>${user.nombre}</div>
                    <div style='font-size: 0.8rem; color: #666;'>${user.rol}</div>
                </div>
                <div style='text-align: right;'>
                    <div style='font-size: 0.8rem; color: ${user.status === "Online" ? "green" : "#888"}; font-weight: bold;'>● ${user.status}</div>
                    <div style='font-size: 0.75rem; color: #999;'>${user.actividad}</div>
                </div>
                <button style='margin-left: 20px; background: none; border: none; color: #ff4757; cursor: pointer;'>✕</button>
            </div>
        `).join('');
    } catch(e) { console.error("Error al cargar equipo"); }
}

function invitarUsuario() {
    const nombre = prompt("Nombre del nuevo miembro:");
    if(nombre) {
        fetch('/api/usuarios/registrar', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({nombre: nombre})
        }).then(r => r.json()).then(data => alert(data.message));
    }
}

// Cargar equipo al entrar a la pestaña
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Usuarios')) setTimeout(loadEquipoDespacho, 150);
    });
});

// Registro del Service Worker para PWA
if ('serviceWorker' in navigator) {
    navigator.serviceWorker.register('/sw.js')
    .then(reg => console.log('Service Worker Registrado ✅'))
    .catch(err => console.log('Error en SW ❌', err));
}

let deferredPrompt;
window.addEventListener('beforeinstallprompt', (e) => {
    e.preventDefault();
    deferredPrompt = e;
    const installBtn = document.getElementById('pwa-install-btn');
    if (installBtn) installBtn.style.display = 'inline-flex';
});

async function installPWAApp() {
    if (!deferredPrompt) {
        alert("Para instalar en iOS: Pulsa 'Compartir' y luego 'Añadir a pantalla de inicio' 📲");
        return;
    }
    deferredPrompt.prompt();
    const { outcome } = await deferredPrompt.userChoice;
    if (outcome === 'accepted') {
        console.log('Usuario instaló la App');
    }
    deferredPrompt = null;
}

document.getElementById('pwa-install-btn')?.addEventListener('click', installPWAApp);

async function ejecutarAgente() {
    const task = document.getElementById('agent-task-input').value;
    if(!task) return;

    const thoughtDiv = document.getElementById('agent-thought-process');
    const stepsLog = document.getElementById('agent-steps-log');
    const finalResult = document.getElementById('agent-final-result');

    thoughtDiv.style.display = 'block';
    finalResult.style.display = 'none';
    stepsLog.innerHTML = "> Iniciando Agente Autónomo...<br>";

    try {
        const r = await fetch('/api/ia/agent-task', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({task: task})
        });
        const data = await r.json();

        // Mostrar pasos con delay para simular pensamiento
        for (const step of data.steps) {
            await new Promise(resolve => setTimeout(resolve, 800));
            stepsLog.innerHTML += `> ${step}<br>`;
        }

        await new Promise(resolve => setTimeout(resolve, 500));
        finalResult.innerText = data.result;
        finalResult.style.display = 'block';
    } catch(e) {
        stepsLog.innerHTML += "<span style='color:red;'>! Error en la conexión con el motor cognitivo.</span>";
    }
}

async function loadAnalyticsData() {
    const section = document.getElementById('analytics');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/analytics/detailed');
        const data = await r.json();
        
        if(data.success) {
            document.getElementById('ana-winrate').innerText = data.performance.win_rate + '%';
            document.getElementById('ana-hours').innerText = data.performance.ahorro_horas_mes + 'h';

            // Gráfica de Tarta (Distribución)
            new Chart(document.getElementById('anaPieChart'), {
                type: 'doughnut',
                data: {
                    labels: data.expedientes_por_tipo.labels,
                    datasets: [{
                        data: data.expedientes_por_tipo.values,
                        backgroundColor: ['#007BFF', '#6610f2', '#6f42c1', '#e83e8c']
                    }]
                },
                options: { plugins: { legend: { position: 'bottom' } } }
            });

            // Gráfica de Barras (ROI)
            new Chart(document.getElementById('anaBarChart'), {
                type: 'bar',
                data: {
                    labels: data.roi_data.labels,
                    datasets: [{
                        label: 'Euros Ahorrados',
                        data: data.roi_data.ahorro_euro,
                        backgroundColor: '#28a745'
                    }]
                }
            });
        }
    } catch(e) { console.error("Error al cargar analytics"); }
}

// Escuchar entrada a la sección
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Analytics')) setTimeout(loadAnalyticsData, 150);
    });
});

async function loadExpedientes() {
    const section = document.getElementById('expedientes');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/expedientes/listar');
        const data = await r.json();
        if(data.success) {
            document.getElementById('current-path-display').innerText = data.current_path;
            const tableBody = document.getElementById('expedientes-table-body');
            
            tableBody.innerHTML = data.files.map(file => `
                <tr style='border-bottom: 1px solid #eee;' onmouseover='this.style.background=\"#fcfcfc\"' onmouseout='this.style.background=\"transparent\"'>
                    <td style='padding:12px; text-align:center;'>${file.is_dir ? '📂' : '📄'}</td>
                    <td style='padding:12px; font-weight:${file.is_dir ? '600' : '400'}; color:${file.is_dir ? 'var(--dark-blue)' : '#333'};'>${file.name}</td>
                    <td style='padding:12px; color:#888; font-size:0.85rem;'>${file.size}</td>
                    <td style='padding:12px; color:#888; font-size:0.85rem;'>${file.mtime}</td>
                    <td style='padding:12px; text-align:center;'>
                        <button onclick='alert(\"Abriendo ${file.name}...\")' style='padding:4px 8px; background:none; border:1px solid #ddd; border-radius:4px; cursor:pointer;'>👁️</button>
                        <button style='padding:4px 8px; background:none; border:1px solid #ddd; border-radius:4px; cursor:pointer;'>⬇️</button>
                    </td>
                </tr>
            `).join('');
        }
    } catch(e) { console.error("Error al listar expedientes"); }
}

// Escuchar entrada a la sección
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Expedientes')) setTimeout(loadExpedientes, 150);
    });
});

async function simularAnalisisLexnet() {
    const btn = event.target;
    btn.innerText = "Calculando plazos...";
    btn.disabled = true;

    try {
        const r = await fetch('/api/lexnet/analizar-plazo', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({dias: 20}) // Simula un plazo de 20 días (ej: Ordinario)
        });
        const data = await r.json();

        if(data.success) {
            document.getElementById('lexnet-results-panel').style.display = 'block';
            document.getElementById('lex-fecha-not').innerText = data.fecha_notificacion;
            document.getElementById('lex-dias').innerText = data.dias_habiles;
            document.getElementById('lex-fecha-venc').innerText = data.fecha_limite;
            
            btn.innerText = "ANÁLISIS COMPLETADO";
            btn.style.background = "green";
        }
    } catch(e) { alert("Error al procesar la notificación"); }
}

async function loadConfig() {
    const section = document.getElementById('config');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/config/get');
        const data = await r.json();
        if(data.success) {
            document.getElementById('conf-ollama').value = data.config.ollama_model;
            document.getElementById('conf-pending').value = data.config.pendientes_dir;
            document.getElementById('conf-fallback').checked = data.config.ia_fallback;
        }
    } catch(e) { console.error("Error al cargar configuración"); }
}

async function saveConfig() {
    const btn = event.target;
    btn.innerText = "Guardando...";
    
    const payload = {
        ollama_model: document.getElementById('conf-ollama').value,
        ia_fallback: document.getElementById('conf-fallback').checked
    };

    try {
        const r = await fetch('/api/config/save', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify(payload)
        });
        const data = await r.json();
        if(data.success) {
            alert(data.message);
            btn.innerText = "GUARDAR CAMBIOS";
        }
    } catch(e) { alert("Error al guardar"); }
}

// Cargar config al entrar a la pestaña
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Configuración')) setTimeout(loadConfig, 150);
    });
});

async function loadDeployStatus() {
    const section = document.getElementById('deploy');
    if (!section || !section.classList.contains('active')) return;

    try {
        const r = await fetch('/api/deploy/status');
        const data = await r.json();
        if(data.success) {
            document.getElementById('svc-db').innerText = data.services.database;
            document.getElementById('svc-ia').innerText = data.services.ollama;
            document.getElementById('svc-storage').innerText = data.services.storage;
            document.getElementById('svc-pwa').innerText = data.services.pwa;
            document.getElementById('svc-uptime').innerText = data.uptime;
            document.getElementById('svc-last').innerText = data.last_deploy;
        }
    } catch(e) { console.error("Error al cargar status de deploy"); }
}

// Escuchar entrada a la sección
document.querySelectorAll('.nav-item').forEach(item => {
    item.addEventListener('click', () => {
        if(item.innerText.includes('Deploy Status')) setTimeout(loadDeployStatus, 150);
    });
});

// ═══════════════════════════════════════════════════════════════
// IA CASCADE - EVENT LISTENERS Y EVENTOS GLOBALES
// ═══════════════════════════════════════════════════════════════

// Event listener para slider de temperature
document.addEventListener('DOMContentLoaded', () => {
    const tempSlider = document.getElementById('test-temperature');
    const tempValue = document.getElementById('temp-value');
    
    if (tempSlider && tempValue) {
        tempSlider.addEventListener('input', (e) => {
            tempValue.textContent = e.target.value;
        });
        console.log('✅ Slider temperature inicializado');
    }
    
    // Cerrar modal al hacer clic fuera
    const modal = document.getElementById('api-key-modal');
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeAPIKeyModal();
            }
        });
    }
});

// Hacer funciones globales accesibles desde HTML
window.loadCascadeStats = loadCascadeStats;
window.testIACascade = testIACascade;
window.refreshCascadeStats = refreshCascadeStats;
window.resetCascadeStats = resetCascadeStats;
window.exportCascadeStats = exportCascadeStats;
window.toggleProvider = toggleProvider;
window.openAPIKeyModal = openAPIKeyModal;
window.closeAPIKeyModal = closeAPIKeyModal;
window.saveAPIKey = saveAPIKey;
window.testProvider = testProvider;

console.log('✅ Funciones IA Cascade expuestas globalmente');

// Auto-refresh stats cuando sección IA Cascade está activa
setInterval(() => {
    const iaCascadeSection = document.getElementById('ia-cascade');
    if (iaCascadeSection && iaCascadeSection.classList.contains('active')) {
        loadCascadeStats();
    }
}, 30000);  // Cada 30 segundos

console.log('✅ Auto-refresh IA Cascade configurado');


// ═══════════════════════════════════════════════════════════════
// IA CASCADE - FUNCIONES GLOBALES (EXPUERTAS PARA HTML)
// ═══════════════════════════════════════════════════════════════

// Hacer TODAS las funciones accesibles desde HTML onclick
window.loadCascadeStats = loadCascadeStats;
window.testIACascade = testIACascade;
window.refreshCascadeStats = refreshCascadeStats;
window.resetCascadeStats = resetCascadeStats;
window.exportCascadeStats = exportCascadeStats;
window.toggleProvider = toggleProvider;
window.openAPIKeyModal = openAPIKeyModal;
window.closeAPIKeyModal = closeAPIKeyModal;
window.saveAPIKey = saveAPIKey;
window.testProvider = testProvider;

console.log('✅ IA CASCADE FUNCIONES GLOBALES ACTIVADAS');

// Event listener para slider de temperature
const tempSlider = document.getElementById('test-temperature');
const tempValue = document.getElementById('temp-value');
if (tempSlider && tempValue) {
    tempSlider.addEventListener('input', (e) => {
        tempValue.textContent = e.target.value;
    });
    console.log('✅ Slider temperature configurado');
}

// Cerrar modal al clic fuera
const modal = document.getElementById('api-key-modal');
if (modal) {
    modal.addEventListener('click', (e) => {
        if (e.target === modal) closeAPIKeyModal();
    });
}

// Auto-refresh cuando sección IA Cascade está activa
setInterval(() => {
    const section = document.getElementById('ia-cascade');
    if (section && section.classList.contains('active')) {
        loadCascadeStats();
    }
}, 30000);

console.log('✅ IA CASCADE COMPLETAMENTE CONFIGURADO');

// ═══════════════════════════════════════════════════════════════
// IA CASCADE - FUNCIONES GLOBALES (CRÍTICO)
// ═══════════════════════════════════════════════════════════════

window.loadCascadeStats = loadCascadeStats;
window.testIACascade = testIACascade;
window.refreshCascadeStats = async () => { await loadCascadeStats(); };
window.resetCascadeStats = async () => {
    if (confirm('¿Resetear stats?')) {
        await fetch('/api/ia-cascade/reset-stats', {method: 'POST'});
        loadCascadeStats();
    }
};
window.exportCascadeStats = async () => {
    const res = await fetch('/api/ia-cascade/stats');
    const data = await res.json();
    const blob = new Blob([JSON.stringify(data.stats, null, 2)], {type: 'application/json'});
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'ia-cascade-stats.json';
    a.click();
};

// Event listener temperatura
const tempSlider = document.getElementById('test-temperature');
const tempValue = document.getElementById('temp-value');
if (tempSlider && tempValue) {
    tempSlider.addEventListener('input', e => tempValue.textContent = e.target.value);
}

console.log('✅ IA CASCADE GLOBAL FUNCTIONS ACTIVATED');

// ═══════════════════════════════════════════════════════════════
// IA CASCADE GLOBAL FUNCTIONS - CRÍTICO
// ═══════════════════════════════════════════════════════════════

window.refreshCascadeStats = async function() {
    console.log('🔄 Refrescando stats...');
    if (typeof loadCascadeStats !== 'undefined') {
        await loadCascadeStats();
    } else {
        const res = await fetch('/api/ia-cascade/stats-public');
        const data = await res.json();
        if (data.success) {
            location.reload();
        }
    }
};

window.resetCascadeStats = async function() {
    if (!confirm('¿Resetear todas las estadísticas?')) return;
    console.log('🗑️ Reseteando stats...');
    try {
        const res = await fetch('/api/ia-cascade/reset-stats', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({})
        });
        const data = await res.json();
        if (data.success) {
            alert('✅ Estadísticas reseteadas');
            window.refreshCascadeStats();
        } else {
            alert('❌ Error: ' + data.error);
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
};

window.exportCascadeStats = async function() {
    console.log('📥 Exportando stats...');
    try {
        const res = await fetch('/api/ia-cascade/stats-public');
        const data = await res.json();
        if (data.success) {
            const blob = new Blob([JSON.stringify(data.stats, null, 2)], {type: 'application/json'});
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `ia-cascade-stats-${Date.now()}.json`;
            a.click();
            URL.revokeObjectURL(url);
            console.log('✅ Stats exportadas');
        }
    } catch (e) {
        alert('❌ Error: ' + e.message);
    }
};

// Event listener para slider temperatura
document.addEventListener('DOMContentLoaded', function() {
    const tempSlider = document.getElementById('test-temperature');
    const tempValue = document.getElementById('temp-value');
    if (tempSlider && tempValue) {
        tempSlider.addEventListener('input', function(e) {
            tempValue.textContent = e.target.value;
        });
        console.log('✅ Slider temperatura configurado');
    }
});

console.log('✅ IA CASCADE FUNCIONES GLOBALES ACTIVADAS');
