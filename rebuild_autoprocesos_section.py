#!/usr/bin/env python3
"""
Reconstruir sección completa de auto-procesos (HTML + JS)
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    contenido = f.read()

import re

# Reemplazar toda la sección de autoprocesos
seccion_nueva = '''        <section id="autoprocesos" class="section">
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
                        🔍 ESCANEAR
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
                    <p style="color: #999; text-align: center; padding: 40px;">Cargando...</p>
                </div>
            </div>
        </section>'''

# Reemplazar
contenido = re.sub(
    r'<section id="autoprocesos" class="section">.*?</section>',
    seccion_nueva,
    contenido,
    flags=re.DOTALL
)

# Eliminar TODAS las funciones JS viejas de autoprocessor
for func in ['loadAutoProcessorStatus', 'startAutoProcessor', 'stopAutoProcessor', 'scanFiles']:
    contenido = re.sub(
        rf'(async )?function {func}\([^)]*\).*?\n\s+\}}',
        '',
        contenido,
        flags=re.DOTALL
    )

# Añadir JS NUEVO y LIMPIO justo antes del último </script>
js_nuevo = '''
        // AUTO-PROCESSOR FUNCTIONS
        function loadAutoProcessorStatus() {
            fetch('/api/autoprocessor/status')
                .then(r => r.json())
                .then(data => {
                    if (data.success) {
                        const s = data.status;
                        document.getElementById('auto-processed').textContent = s.stats.processed || 0;
                        document.getElementById('auto-pending').textContent = s.queue || 0;
                        document.getElementById('auto-errors').textContent = s.stats.errors || 0;
                        document.getElementById('auto-running').textContent = s.running ? '▶️' : '⏸️';
                        
                        document.getElementById('auto-status').innerHTML = 
                            '<p><strong>Estado:</strong> ' + (s.running ? '🟢 ACTIVO' : '🔴 DETENIDO') + '</p>' +
                            '<p><strong>Carpeta:</strong> ' + s.watch_dir + '</p>' +
                            '<p><strong>Procesados:</strong> ' + (s.stats.processed||0) + '</p>' +
                            '<p><strong>En Cola:</strong> ' + (s.queue||0) + '</p>';
                        
                        document.getElementById('processing-queue').innerHTML = 
                            s.queue_items && s.queue_items.length > 0 
                            ? s.queue_items.map(i => '<div style="padding:10px;border-bottom:1px solid #eee">' + i.file.split('/').pop() + '</div>').join('')
                            : '<p style="color:#999;text-align:center;padding:40px">✅ No hay archivos</p>';
                    }
                })
                .catch(e => console.error(e));
        }
        
        function startAutoProcessor() {
            fetch('/api/autoprocessor/start', {method:'POST'})
                .then(r => r.json())
                .then(d => { alert(d.message); loadAutoProcessorStatus(); });
        }
        
        function stopAutoProcessor() {
            fetch('/api/autoprocessor/stop', {method:'POST'})
                .then(r => r.json())
                .then(d => { alert(d.message); loadAutoProcessorStatus(); });
        }
        
        function scanFiles() {
            if (!confirm('¿Escanear archivos?')) return;
            fetch('/api/autoprocessor/scan', {method:'POST'})
                .then(r => r.json())
                .then(d => { alert(d.message); loadAutoProcessorStatus(); });
        }
        
        // Auto-cargar cuando se abre el tab
        const origShowTab = window.showTab;
        window.showTab = function(tab) {
            origShowTab(tab);
            if (tab === 'autoprocesos') {
                loadAutoProcessorStatus();
                setInterval(function() {
                    if (document.getElementById('autoprocesos').classList.contains('active')) {
                        loadAutoProcessorStatus();
                    }
                }, 5000);
            }
        };
'''

# Insertar antes del último </script>
partes = contenido.rsplit('</script>', 1)
if len(partes) == 2:
    contenido = partes[0] + js_nuevo + '\n    </script>' + partes[1]

# Guardar
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Módulo Auto-Procesos completamente reconstruido")
print("   - HTML limpio")
print("   - JavaScript minificado y funcional")
print("   - Auto-actualización cada 5 segundos")

