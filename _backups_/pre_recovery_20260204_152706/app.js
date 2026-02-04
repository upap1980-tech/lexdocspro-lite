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
    const clickedBtn = event.target;
    clickedBtn.classList.add('active');
    document.getElementById(`tab-${tabName}`).classList.add('active');
    
    updateStatus(`Pestaña: ${tabName === 'consulta' ? 'Consultas' : tabName === 'documentos' ? 'Generador de Documentos' : 'Analizador LexNET'}`);
}

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

function copyLexNetAnalysis() {}
function downloadLexNetAnalysis() {}
function exportToiCloud() {}
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
            updateStatus(`📄 Procesando ${i+1}/${lexnetMultipleFiles.length}: ${file.name}...`);
            
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
            {name: 'juzgado', label: 'Juzgado', type: 'text', placeholder: 'Juzgado de Primera Instancia nº...'},
            {name: 'demandante', label: 'Demandante', type: 'text', placeholder: 'Nombre completo'},
            {name: 'demandado', label: 'Demandado', type: 'text', placeholder: 'Nombre completo'},
            {name: 'hechos', label: 'Hechos', type: 'textarea', placeholder: 'Narración de los hechos...'},
            {name: 'petitorio', label: 'Petitorio', type: 'textarea', placeholder: 'Se solicita que...'}
        ]
    },
    contestacion_demanda: {
        name: 'Contestación a la Demanda',
        icon: '🛡️',
        desc: 'Respuesta formal a demanda civil',
        fields: [
            {name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento ordinario nº...'},
            {name: 'demandado', label: 'Demandado (quien contesta)', type: 'text', placeholder: 'Nombre completo'},
            {name: 'hechos_propios', label: 'Hechos propios', type: 'textarea', placeholder: 'Versión de los hechos...'},
            {name: 'excepciones', label: 'Excepciones y defensas', type: 'textarea', placeholder: 'Defensas jurídicas...'},
            {name: 'suplica', label: 'Súplica', type: 'textarea', placeholder: 'Se solicita la desestimación...'}
        ]
    },
    recurso_apelacion: {
        name: 'Recurso de Apelación',
        icon: '🔄',
        desc: 'Recurso contra sentencia de primera instancia',
        fields: [
            {name: 'sentencia', label: 'Sentencia a recurrir', type: 'text', placeholder: 'Sentencia nº... de fecha...'},
            {name: 'recurrente', label: 'Recurrente', type: 'text', placeholder: 'Nombre completo'},
            {name: 'fundamentos', label: 'Fundamentos de Derecho', type: 'textarea', placeholder: 'Infracciones cometidas...'},
            {name: 'suplica', label: 'Súplica', type: 'textarea', placeholder: 'Se suplica la revocación...'}
        ]
    },
    recurso_reposicion: {
        name: 'Recurso de Reposición',
        icon: '🔁',
        desc: 'Recurso contra autos y providencias',
        fields: [
            {name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...'},
            {name: 'resolucion', label: 'Resolución recurrida', type: 'text', placeholder: 'Auto/Providencia de fecha...'},
            {name: 'recurrente', label: 'Recurrente', type: 'text', placeholder: 'Nombre completo'},
            {name: 'motivos', label: 'Motivos del recurso', type: 'textarea', placeholder: 'Fundamentos del recurso...'}
        ]
    },
    escrito_alegaciones: {
        name: 'Escrito de Alegaciones',
        icon: '📝',
        desc: 'Respuesta a trámite de alegaciones',
        fields: [
            {name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...'},
            {name: 'parte', label: 'En nombre de', type: 'text', placeholder: 'Nombre de la parte'},
            {name: 'alegaciones', label: 'Alegaciones', type: 'textarea', placeholder: 'Contenido de las alegaciones...'}
        ]
    },
    desistimiento: {
        name: 'Desistimiento',
        icon: '🚫',
        desc: 'Escrito de desistimiento del procedimiento',
        fields: [
            {name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...'},
            {name: 'parte', label: 'Parte que desiste', type: 'text', placeholder: 'Nombre completo'},
            {name: 'motivo', label: 'Motivo (opcional)', type: 'textarea', placeholder: 'Por convenir a mis intereses...'}
        ]
    },
    personacion: {
        name: 'Personación y Solicitud de Copias',
        icon: '👤',
        desc: 'Primera comparecencia en autos',
        fields: [
            {name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...'},
            {name: 'parte', label: 'En nombre de', type: 'text', placeholder: 'Nombre del representado'},
            {name: 'procurador', label: 'Procurador', type: 'text', placeholder: 'Nombre del procurador'},
            {name: 'abogado', label: 'Abogado', type: 'text', placeholder: 'Nombre del abogado'}
        ]
    },
    poder_procesal: {
        name: 'Poder para Pleitos',
        icon: '📜',
        desc: 'Otorgamiento de poder procesal',
        fields: [
            {name: 'poderdante', label: 'Poderdante', type: 'text', placeholder: 'Nombre completo'},
            {name: 'apoderado', label: 'Apoderado (Procurador)', type: 'text', placeholder: 'Nombre del procurador'},
            {name: 'dni_poderdante', label: 'DNI Poderdante', type: 'text', placeholder: '12345678A'},
            {name: 'ambito', label: 'Ámbito del poder', type: 'text', placeholder: 'General o específico'}
        ]
    },
    escrito_prueba: {
        name: 'Proposición de Prueba',
        icon: '🔬',
        desc: 'Escrito de proposición de medios de prueba',
        fields: [
            {name: 'procedimiento', label: 'Nº Procedimiento', type: 'text', placeholder: 'Procedimiento nº...'},
            {name: 'parte', label: 'Parte que propone', type: 'text', placeholder: 'Nombre de la parte'},
            {name: 'hechos', label: 'Hechos a probar', type: 'textarea', placeholder: 'Hechos controvertidos...'},
            {name: 'pruebas', label: 'Medios de prueba', type: 'textarea', placeholder: 'Documental, testifical, pericial...'}
        ]
    },
    burofax: {
        name: 'Burofax',
        icon: '📮',
        desc: 'Comunicación fehaciente por burofax',
        fields: [
            {name: 'remitente', label: 'Remitente', type: 'text', placeholder: 'Nombre y dirección completa'},
            {name: 'destinatario', label: 'Destinatario', type: 'text', placeholder: 'Nombre y dirección completa'},
            {name: 'asunto', label: 'Asunto', type: 'text', placeholder: 'Resumen del asunto'},
            {name: 'contenido', label: 'Contenido', type: 'textarea', placeholder: 'Texto del burofax...'}
        ]
    },
    requerimiento: {
        name: 'Requerimiento Extrajudicial',
        icon: '⚠️',
        desc: 'Requerimiento previo a reclamación judicial',
        fields: [
            {name: 'requirente', label: 'Requirente', type: 'text', placeholder: 'Quien requiere'},
            {name: 'requerido', label: 'Requerido', type: 'text', placeholder: 'Destinatario'},
            {name: 'objeto', label: 'Objeto del requerimiento', type: 'textarea', placeholder: 'Contenido del requerimiento...'},
            {name: 'plazo', label: 'Plazo', type: 'text', placeholder: 'Ej: 10 días hábiles'}
        ]
    },
    querella: {
        name: 'Querella Criminal',
        icon: '⚔️',
        desc: 'Escrito de querella penal',
        fields: [
            {name: 'querellante', label: 'Querellante', type: 'text', placeholder: 'Nombre completo'},
            {name: 'querellado', label: 'Querellado', type: 'text', placeholder: 'Nombre completo'},
            {name: 'hechos', label: 'Hechos denunciados', type: 'textarea', placeholder: 'Narración cronológica...'},
            {name: 'delito', label: 'Delito/s', type: 'text', placeholder: 'Ej: Estafa (art. 248 CP)'},
            {name: 'pruebas', label: 'Pruebas', type: 'textarea', placeholder: 'Medios probatorios...'}
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

