let currentFile = null;
let ocrText = '';
document.addEventListener('DOMContentLoaded', () => {
    refreshFiles();
    addMessage('system', '¡Bienvenido a LexDocsPro LITE! Selecciona un PDF para empezar.');
    const promptInput = document.getElementById('chatPrompt');
    if (promptInput) {
        promptInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
        });
    }
});
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
    pathDiv.textContent = data.current_path || 'Raíz';
    tree.innerHTML = '';
    if (data.current_path) {
        const upBtn = document.createElement('div');
        upBtn.className = 'folder';
        upBtn.textContent = '📁 .. (Subir)';
        upBtn.onclick = () => { const parent = data.current_path.split('/').slice(0, -1).join('/'); refreshFiles(parent); };
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
async function runOCR() {
    if (!currentFile) return;
    try {
        updateStatus('🔍 Ejecutando OCR...');
        const btnOCR = document.getElementById('btnOCR');
        btnOCR.disabled = true;
        btnOCR.innerHTML = '<span class="loading"></span> Procesando...';
        const response = await fetch('/api/ocr', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ filename: currentFile.path }) });
        const data = await response.json();
        if (data.text) {
            ocrText = data.text;
            addMessage('system', `✅ OCR: ${data.text.length} caracteres`);
            addMessage('assistant', `Documento "${currentFile.name}" procesado. ¿En qué puedo ayudarte?`);
            updateStatus('✅ OCR completado');
        } else {
            addMessage('system', '⚠️ No se pudo extraer texto');
            updateStatus('⚠️ OCR sin resultados');
        }
    } catch (error) {
        console.error('Error:', error);
        addMessage('system', '❌ Error en OCR');
        updateStatus('❌ Error en OCR');
    } finally {
        const btnOCR = document.getElementById('btnOCR');
        btnOCR.disabled = false;
        btnOCR.textContent = '🔍 Ejecutar OCR';
    }
}
async function sendMessage() {
    const promptInput = document.getElementById('chatPrompt');
    const prompt = promptInput.value.trim();
    if (!prompt) return;
    addMessage('user', prompt);
    promptInput.value = '';
    const loadingId = addMessage('assistant', '<span class="loading"></span> Pensando...');
    updateStatus('💬 Consultando IA...');
    try {
        const response = await fetch('/api/chat', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ prompt: prompt, context: ocrText }) });
        const data = await response.json();
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) { loadingMsg.textContent = data.response; }
        updateStatus('Listo');
    } catch (error) {
        console.error('Error:', error);
        const loadingMsg = document.getElementById(loadingId);
        if (loadingMsg) { loadingMsg.textContent = '❌ Error al conectar con IA'; }
        updateStatus('❌ Error en chat');
    }
}
function addMessage(type, text) {
    const container = document.getElementById('chatMessages');
    const msgId = 'msg-' + Date.now();
    const div = document.createElement('div');
    div.id = msgId;
    div.className = `message ${type}`;
    div.innerHTML = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return msgId;
}
function updateStatus(text) {
    document.getElementById('status').textContent = text;
}
