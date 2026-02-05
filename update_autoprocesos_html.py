#!/usr/bin/env python3
"""
Actualizar sección de auto-procesos en index.html
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar y reemplazar el placeholder de autoprocesos
nuevo_modulo = '''        <section id="autoprocesos" class="section">
            <h1 style="margin-bottom: 30px; color: #333;">🤖 Auto-Procesos</h1>
            
            <!-- Control Panel -->
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-bottom: 20px;">
                <h3 style="margin-bottom: 20px;">Panel de Control</h3>
                
                <div style="display: flex; gap: 15px; margin-bottom: 20px;">
                    <button onclick="startAutoProcessor()" style="padding: 10px 20px; background: #28a745; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                        ▶️ INICIAR
                    </button>
                    <button onclick="stopAutoProcessor()" style="padding: 10px 20px; background: #dc3545; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                        ⏸️ DETENER
                    </button>
                    <button onclick="scanFiles()" style="padding: 10px 20px; background: #007BFF; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                        🔍 ESCANEAR AHORA
                    </button>
                    <button onclick="loadAutoProcessorStatus()" style="padding: 10px 20px; background: #6c757d; color: white; border: none; border-radius: 6px; cursor: pointer; font-weight: bold;">
                        🔄 ACTUALIZAR
                    </button>
                </div>
                
                <div id="auto-status" style="padding: 15px; background: #f8f9fa; border-radius: 6px; font-family: monospace;">
                    <p>🔄 Cargando estado...</p>
                </div>
            </div>
            
            <!-- Estadísticas -->
            <div class="kpi-grid">
                <div class="kpi-card success">
                    <h3>Procesados</h3>
                    <span class="kpi-value" id="auto-processed">0</span>
                </div>
                <div class="kpi-card warning">
                    <h3>En Cola</h3>
                    <span class="kpi-value" id="auto-pending">0</span>
                </div>
                <div class="kpi-card danger">
                    <h3>Errores</h3>
                    <span class="kpi-value" id="auto-errors">0</span>
                </div>
                <div class="kpi-card info">
                    <h3>Estado</h3>
                    <span class="kpi-value" id="auto-running" style="font-size: 1.5rem;">⏸️</span>
                </div>
            </div>
            
            <!-- Cola de Procesamiento -->
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-top: 20px;">
                <h3 style="margin-bottom: 15px;">Cola de Procesamiento</h3>
                <div id="processing-queue" style="max-height: 300px; overflow-y: auto;">
                    <p style="color: #999; text-align: center; padding: 40px;">No hay archivos en cola</p>
                </div>
            </div>
        </section>'''

# Reemplazar
import re
patron = r'<section id="autoprocesos" class="section">.*?</section>'
contenido = re.sub(patron, nuevo_modulo, contenido, flags=re.DOTALL)

# Añadir JavaScript al final (antes de </body>)
javascript_auto = '''
    <script>
        // ═══════════════════════════════════════════════════════════════
        // AUTO-PROCESSOR FUNCTIONS
        // ═══════════════════════════════════════════════════════════════
        
        async function loadAutoProcessorStatus() {
            try {
                const response = await fetch('/api/autoprocessor/status', {
                    credentials: 'include'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const status = data.status;
                    
                    // Actualizar KPIs
                    document.getElementById('auto-processed').textContent = status.stats.processed;
                    document.getElementById('auto-pending').textContent = status.queue;
                    document.getElementById('auto-errors').textContent = status.stats.errors;
                    document.getElementById('auto-running').textContent = status.running ? '▶️' : '⏸️';
                    
                    // Actualizar panel de estado
                    const statusDiv = document.getElementById('auto-status');
                    statusDiv.innerHTML = `
                        <p><strong>Estado:</strong> ${status.running ? '🟢 ACTIVO' : '🔴 DETENIDO'}</p>
                        <p><strong>Carpeta:</strong> ${status.watch_dir}</p>
                        <p><strong>Procesados:</strong> ${status.stats.processed}</p>
                        <p><strong>Errores:</strong> ${status.stats.errors}</p>
                        <p><strong>En Cola:</strong> ${status.queue}</p>
                        <p><strong>Último:</strong> ${status.stats.last_processed || 'N/A'}</p>
                        <p><strong>Inicio:</strong> ${status.stats.start_time || 'N/A'}</p>
                    `;
                    
                    // Actualizar cola
                    const queueDiv = document.getElementById('processing-queue');
                    if (status.queue_items && status.queue_items.length > 0) {
                        queueDiv.innerHTML = status.queue_items.map(item => `
                            <div style="padding: 10px; border-bottom: 1px solid #eee;">
                                <strong>${item.file.split('/').pop()}</strong>
                                <span style="color: #999; float: right;">${item.status}</span>
                            </div>
                        `).join('');
                    } else {
                        queueDiv.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">No hay archivos en cola</p>';
                    }
                    
                    console.log('✅ Auto-processor status actualizado');
                }
            } catch (error) {
                console.error('❌ Error cargando auto-processor status:', error);
            }
        }
        
        async function startAutoProcessor() {
            try {
                const response = await fetch('/api/autoprocessor/start', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                const data = await response.json();
                alert(data.message);
                loadAutoProcessorStatus();
            } catch (error) {
                alert('Error iniciando auto-processor');
                console.error(error);
            }
        }
        
        async function stopAutoProcessor() {
            try {
                const response = await fetch('/api/autoprocessor/stop', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                const data = await response.json();
                alert(data.message);
                loadAutoProcessorStatus();
            } catch (error) {
                alert('Error deteniendo auto-processor');
                console.error(error);
            }
        }
        
        async function scanFiles() {
            if (!confirm('¿Escanear y procesar todos los archivos en la carpeta PENDIENTES?')) {
                return;
            }
            
            try {
                const response = await fetch('/api/autoprocessor/scan', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert(`✅ ${data.processed} archivos procesados`);
                    loadAutoProcessorStatus();
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (error) {
                alert('Error escaneando archivos');
                console.error(error);
            }
        }
        
        // Auto-actualizar cada 5 segundos si el tab está activo
        setInterval(() => {
            const section = document.getElementById('autoprocesos');
            if (section.classList.contains('active')) {
                loadAutoProcessorStatus();
            }
        }, 5000);
    </script>
'''

# Insertar antes de </body>
contenido = contenido.replace('</body>', javascript_auto + '\n</body>')

# Guardar
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Módulo Auto-Procesos actualizado en index.html")

