#!/usr/bin/env python3
"""
Reemplazar completamente el JavaScript de auto-procesos
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Eliminar todo el JavaScript de auto-procesos existente
import re
contenido = re.sub(
    r'// ═+\n\s+// AUTO-PROCESSOR FUNCTIONS.*?// ═+',
    '',
    contenido,
    flags=re.DOTALL
)

# Eliminar funciones individuales si quedaron
for func in ['loadAutoProcessorStatus', 'startAutoProcessor', 'stopAutoProcessor', 'scanFiles']:
    contenido = re.sub(
        rf'async function {func}\(\).*?\n\s+\}}',
        '',
        contenido,
        flags=re.DOTALL
    )

# Eliminar setInterval viejo
contenido = re.sub(
    r'setInterval\(\(\) => \{.*?autoprocesos.*?\}, \d+\);',
    '',
    contenido,
    flags=re.DOTALL
)

# Añadir nuevo JavaScript COMPLETO justo antes de </script> final
nuevo_js = '''
        // ═══════════════════════════════════════════════════════════════
        // AUTO-PROCESSOR FUNCTIONS (v3.2 - Fixed)
        // ═══════════════════════════════════════════════════════════════
        
        async function loadAutoProcessorStatus() {
            try {
                console.log('🔄 Cargando auto-processor status...');
                
                const response = await fetch('/api/autoprocessor/status', {
                    method: 'GET',
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('📦 Status recibido:', data);
                
                if (data.success && data.status) {
                    const status = data.status;
                    
                    // Actualizar KPIs
                    document.getElementById('auto-processed').textContent = status.stats.processed || 0;
                    document.getElementById('auto-pending').textContent = status.queue || 0;
                    document.getElementById('auto-errors').textContent = status.stats.errors || 0;
                    document.getElementById('auto-running').textContent = status.running ? '▶️' : '⏸️';
                    
                    // Actualizar panel de estado
                    const statusDiv = document.getElementById('auto-status');
                    statusDiv.innerHTML = `
                        <p><strong>Estado:</strong> ${status.running ? '🟢 ACTIVO' : '🔴 DETENIDO'}</p>
                        <p><strong>Carpeta:</strong> ${status.watch_dir}</p>
                        <p><strong>Procesados:</strong> ${status.stats.processed || 0}</p>
                        <p><strong>Errores:</strong> ${status.stats.errors || 0}</p>
                        <p><strong>En Cola:</strong> ${status.queue || 0}</p>
                        <p><strong>Último:</strong> ${status.stats.last_processed || 'N/A'}</p>
                        <p><strong>Iniciado:</strong> ${status.stats.start_time ? new Date(status.stats.start_time).toLocaleString('es-ES') : 'N/A'}</p>
                    `;
                    
                    // Actualizar cola
                    const queueDiv = document.getElementById('processing-queue');
                    if (status.queue_items && status.queue_items.length > 0) {
                        queueDiv.innerHTML = status.queue_items.map(item => `
                            <div style="padding: 10px; border-bottom: 1px solid #eee;">
                                <strong>${item.file.split('/').pop()}</strong>
                                <span style="color: #999; float: right;">${item.status}</span>
                                <br><small style="color: #999;">${item.added_at}</small>
                            </div>
                        `).join('');
                    } else {
                        queueDiv.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">✅ No hay archivos en cola</p>';
                    }
                    
                    console.log('✅ Status actualizado correctamente');
                } else {
                    console.warn('⚠️ Status sin success o data.status');
                    throw new Error(data.error || 'Respuesta inválida');
                }
                
            } catch (error) {
                console.error('❌ Error cargando status:', error);
                
                const statusDiv = document.getElementById('auto-status');
                if (statusDiv) {
                    statusDiv.innerHTML = `
                        <p style="color: #dc3545;">❌ Error: ${error.message}</p>
                        <p style="font-size: 0.8rem; color: #999;">Verifica que el servidor esté corriendo</p>
                    `;
                }
            }
        }
        
        async function startAutoProcessor() {
            try {
                console.log('▶️ Iniciando auto-processor...');
                
                const response = await fetch('/api/autoprocessor/start', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('📦 Respuesta start:', data);
                
                if (data.success) {
                    alert(data.message || '✅ Auto-procesador iniciado');
                    await loadAutoProcessorStatus();
                } else {
                    alert('❌ Error: ' + (data.error || 'Error desconocido'));
                }
                
            } catch (error) {
                console.error('❌ Error:', error);
                alert('❌ Error iniciando auto-processor:\n' + error.message);
            }
        }
        
        async function stopAutoProcessor() {
            try {
                console.log('⏸️ Deteniendo auto-processor...');
                
                const response = await fetch('/api/autoprocessor/stop', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('📦 Respuesta stop:', data);
                
                if (data.success) {
                    alert(data.message || '🛑 Auto-procesador detenido');
                    await loadAutoProcessorStatus();
                } else {
                    alert('❌ Error: ' + (data.error || 'Error desconocido'));
                }
                
            } catch (error) {
                console.error('❌ Error:', error);
                alert('❌ Error deteniendo auto-processor:\n' + error.message);
            }
        }
        
        async function scanFiles() {
            if (!confirm('¿Escanear y procesar todos los archivos en PENDIENTES_LEXDOCS?')) {
                return;
            }
            
            try {
                console.log('🔍 Escaneando archivos...');
                
                const response = await fetch('/api/autoprocessor/scan', {
                    method: 'POST',
                    credentials: 'include'
                });
                
                if (!response.ok) {
                    throw new Error(`HTTP ${response.status}`);
                }
                
                const data = await response.json();
                console.log('📦 Respuesta scan:', data);
                
                if (data.success) {
                    const msg = data.message || `✅ ${data.processed} archivo(s) procesados`;
                    alert(msg);
                    await loadAutoProcessorStatus();
                } else {
                    alert('❌ Error: ' + (data.error || 'Error desconocido'));
                }
                
            } catch (error) {
                console.error('❌ Error:', error);
                alert('❌ Error escaneando archivos:\n' + error.message);
            }
        }
        
        // Auto-actualizar cuando el tab está activo
        let autoProcessorInterval = null;
        
        function startAutoProcessorPolling() {
            if (autoProcessorInterval) {
                clearInterval(autoProcessorInterval);
            }
            
            autoProcessorInterval = setInterval(() => {
                const section = document.getElementById('autoprocesos');
                if (section && section.classList.contains('active')) {
                    loadAutoProcessorStatus();
                }
            }, 5000);
        }
        
        // Iniciar polling cuando se carga el módulo
        const originalShowTab = window.showTab;
        window.showTab = function(tabName) {
            originalShowTab(tabName);
            
            if (tabName === 'autoprocesos') {
                loadAutoProcessorStatus();
                startAutoProcessorPolling();
            }
        };
'''

# Insertar antes del último </script>
# Buscar el último </script> antes de </body>
partes = contenido.rsplit('</script>', 1)
if len(partes) == 2:
    contenido = partes[0] + nuevo_js + '\n    </script>' + partes[1]
else:
    print("⚠️ No se encontró </script>")

# Guardar
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ JavaScript completamente reemplazado")
print("   - Manejo de errores mejorado")
print("   - Logging completo en consola")
print("   - Auto-actualización cada 5 segundos")

