#!/usr/bin/env python3
"""
Restaurar función loadAutoProcessorStatus que se rompió
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    contenido = f.read()

import re

# Eliminar la función loadAutoProcessorStatus existente (está rota)
contenido = re.sub(
    r'async function loadAutoProcessorStatus\(\).*?\n\s+\}',
    '',
    contenido,
    flags=re.DOTALL
)

contenido = re.sub(
    r'function loadAutoProcessorStatus\(\).*?\n\s+\}',
    '',
    contenido,
    flags=re.DOTALL
)

# Añadir versión FUNCIONAL nueva
nueva_funcion = '''
        function loadAutoProcessorStatus() {
            console.log('🔄 Cargando auto-processor status...');
            
            fetch('/api/autoprocessor/status', {
                method: 'GET',
                credentials: 'include'
            })
            .then(response => {
                if (!response.ok) throw new Error('HTTP ' + response.status);
                return response.json();
            })
            .then(data => {
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
                    statusDiv.innerHTML = 
                        '<p><strong>Estado:</strong> ' + (status.running ? '🟢 ACTIVO' : '🔴 DETENIDO') + '</p>' +
                        '<p><strong>Carpeta:</strong> ' + status.watch_dir + '</p>' +
                        '<p><strong>Procesados:</strong> ' + (status.stats.processed || 0) + '</p>' +
                        '<p><strong>Errores:</strong> ' + (status.stats.errors || 0) + '</p>' +
                        '<p><strong>En Cola:</strong> ' + (status.queue || 0) + '</p>' +
                        '<p><strong>Último:</strong> ' + (status.stats.last_processed || 'N/A') + '</p>' +
                        '<p><strong>Iniciado:</strong> ' + (status.stats.start_time || 'N/A') + '</p>';
                    
                    // Actualizar cola
                    const queueDiv = document.getElementById('processing-queue');
                    if (status.queue_items && status.queue_items.length > 0) {
                        queueDiv.innerHTML = status.queue_items.map(function(item) {
                            return '<div style="padding: 10px; border-bottom: 1px solid #eee;">' +
                                   '<strong>' + item.file.split('/').pop() + '</strong>' +
                                   '<span style="color: #999; float: right;">' + item.status + '</span>' +
                                   '</div>';
                        }).join('');
                    } else {
                        queueDiv.innerHTML = '<p style="color: #999; text-align: center; padding: 40px;">✅ No hay archivos en cola</p>';
                    }
                    
                    console.log('✅ Status actualizado correctamente');
                } else {
                    throw new Error(data.error || 'Respuesta inválida');
                }
            })
            .catch(function(error) {
                console.error('❌ Error:', error);
                const statusDiv = document.getElementById('auto-status');
                if (statusDiv) {
                    statusDiv.innerHTML = '<p style="color: #dc3545;">❌ Error: ' + error.message + '</p>' +
                                         '<p style="font-size: 0.8rem; color: #999;">Verifica que el servidor esté corriendo</p>';
                }
            });
        }
'''

# Buscar donde insertar (antes de las otras funciones de autoprocessor)
if 'function startAutoProcessor' in contenido:
    contenido = contenido.replace(
        'function startAutoProcessor',
        nueva_funcion + '\n        function startAutoProcessor'
    )
else:
    # Insertar antes del último </script>
    contenido = contenido.replace('</script>', nueva_funcion + '\n    </script>', 1)

# Guardar
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Función loadAutoProcessorStatus restaurada")

