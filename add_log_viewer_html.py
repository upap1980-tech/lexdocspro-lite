#!/usr/bin/env python3
"""
Añadir visualizador de logs al módulo Auto-Procesos
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar la sección de auto-procesos y añadir tabla de logs
import re

# Buscar el final de "Cola de Procesamiento"
patron = r'(<div id="processing-queue".*?</div>\s*</div>)'

reemplazo = r'''\1

            <!-- Historial de Procesamiento -->
            <div style="background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); margin-top: 20px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                    <h3>Historial de Procesamiento</h3>
                    <button onclick="loadProcessingLog()" style="padding: 8px 15px; background: #007BFF; color: white; border: none; border-radius: 4px; cursor: pointer;">
                        🔄 Actualizar
                    </button>
                </div>
                <div id="processing-log" style="overflow-x: auto;">
                    <p style="color: #999; text-align: center; padding: 40px;">Cargando historial...</p>
                </div>
            </div>'''

contenido = re.sub(patron, reemplazo, contenido, flags=re.DOTALL)

# Añadir función JavaScript
js_log = '''
        function loadProcessingLog() {
            fetch('/api/autoprocessor/log?limit=20')
                .then(r => r.json())
                .then(data => {
                    if (data.success && data.log && data.log.length > 0) {
                        const logHTML = `
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.9rem;">
                                <thead>
                                    <tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
                                        <th style="padding: 10px; text-align: left;">Archivo</th>
                                        <th style="padding: 10px; text-align: center;">Estado</th>
                                        <th style="padding: 10px; text-align: center;">OCR</th>
                                        <th style="padding: 10px; text-align: center;">Tiempo</th>
                                        <th style="padding: 10px; text-align: left;">Fecha</th>
                                        <th style="padding: 10px; text-align: center;">Rutas</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${data.log.map(item => `
                                        <tr style="border-bottom: 1px solid #eee;">
                                            <td style="padding: 10px; max-width: 200px; overflow: hidden; text-overflow: ellipsis;" title="${item.filename}">
                                                ${item.filename}
                                            </td>
                                            <td style="padding: 10px; text-align: center;">
                                                <span style="padding: 4px 8px; border-radius: 4px; background: ${item.status === 'SUCCESS' ? '#d4edda' : '#f8d7da'}; color: ${item.status === 'SUCCESS' ? '#155724' : '#721c24'}; font-size: 0.8rem; font-weight: bold;">
                                                    ${item.status}
                                                </span>
                                            </td>
                                            <td style="padding: 10px; text-align: center;">
                                                ${item.ocr_chars ? item.ocr_chars + ' chars' : '-'}
                                            </td>
                                            <td style="padding: 10px; text-align: center;">
                                                ${item.processing_time ? item.processing_time.toFixed(2) + 's' : '-'}
                                            </td>
                                            <td style="padding: 10px; font-size: 0.85rem; color: #666;">
                                                ${item.completed_at ? new Date(item.completed_at).toLocaleString('es-ES') : '-'}
                                            </td>
                                            <td style="padding: 10px; text-align: center;">
                                                <button onclick="showFilePaths('${item.filename}', '${item.backup_path}', '${item.final_path}')" style="padding: 4px 8px; background: #6c757d; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem;">
                                                    📂 Ver
                                                </button>
                                            </td>
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        `;
                        
                        document.getElementById('processing-log').innerHTML = logHTML;
                    } else {
                        document.getElementById('processing-log').innerHTML = 
                            '<p style="color: #999; text-align: center; padding: 40px;">No hay registros en el historial</p>';
                    }
                })
                .catch(e => {
                    console.error('Error cargando log:', e);
                    document.getElementById('processing-log').innerHTML = 
                        '<p style="color: #dc3545; text-align: center; padding: 40px;">❌ Error cargando historial</p>';
                });
        }
        
        function showFilePaths(filename, backup, final) {
            alert('📂 Trazabilidad de: ' + filename + '\\n\\n' +
                  '💾 Backup:\\n' + backup + '\\n\\n' +
                  '✅ Final:\\n' + final);
        }
        
        // Cargar log cuando se abre el tab
        const origShowTab3 = window.showTab;
        window.showTab = function(tab) {
            origShowTab3(tab);
            if (tab === 'autoprocesos') {
                loadAutoProcessorStatus();
                loadProcessingLog();
            }
        };
'''

# Insertar JS
partes = contenido.rsplit('</script>', 1)
if len(partes) == 2:
    contenido = partes[0] + js_log + '\n    </script>' + partes[1]

with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Visualizador de logs añadido")
print("   - Tabla con últimos 20 registros")
print("   - Estado, tiempos, rutas")
print("   - Botón para ver trazabilidad completa")

