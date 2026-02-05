#!/usr/bin/env python3
"""
Eliminar TODAS las funciones de autoprocessor y crear UNA versión limpia
"""

with open('templates/index.html', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

print(f"📄 Archivo tiene {len(lineas)} líneas")

# PASO 1: Eliminar TODAS las líneas que contengan funciones de autoprocessor
nuevas_lineas = []
skip_until = None
in_function = False
brace_count = 0

for i, linea in enumerate(lineas):
    linea_num = i + 1
    
    # Detectar inicio de función autoprocessor
    if any(func in linea for func in [
        'function loadAutoProcessorStatus',
        'function startAutoProcessor',
        'function stopAutoProcessor', 
        'function scanFiles'
    ]):
        print(f"🗑️  Eliminando función en línea {linea_num}")
        in_function = True
        brace_count = 0
        continue
    
    # Si estamos dentro de una función, contar llaves
    if in_function:
        brace_count += linea.count('{')
        brace_count -= linea.count('}')
        
        # Si volvemos a balance 0 o negativo, terminó la función
        if brace_count <= 0 and '}' in linea:
            in_function = False
            print(f"   ✓ Función terminada en línea {linea_num}")
        continue
    
    # Eliminar líneas con await loadAutoProcessorStatus
    if 'await loadAutoProcessorStatus' in linea or \
       'loadAutoProcessorStatus();' in linea and 'onclick' not in linea:
        print(f"🗑️  Eliminando llamada en línea {linea_num}")
        continue
    
    # Eliminar bloques de comentarios AUTO-PROCESSOR
    if '// AUTO-PROCESSOR FUNCTIONS' in linea or \
       '// ═══' in linea and 'AUTO' in lineas[min(i+1, len(lineas)-1)]:
        skip_until = '// ═══'
        continue
    
    if skip_until and skip_until in linea:
        skip_until = None
        continue
    
    if skip_until:
        continue
    
    # Guardar línea
    nuevas_lineas.append(linea)

print(f"📄 Resultado: {len(nuevas_lineas)} líneas")

# PASO 2: Añadir versión LIMPIA y ÚNICA
js_limpio = '''
        // ═══════════════════════════════════════════════════════════════
        // AUTO-PROCESSOR FUNCTIONS (ÚNICA VERSIÓN)
        // ═══════════════════════════════════════════════════════════════
        
        function loadAutoProcessorStatus() {
            fetch('/api/autoprocessor/status')
                .then(function(response) { return response.json(); })
                .then(function(data) {
                    if (data.success && data.status) {
                        var s = data.status;
                        
                        // KPIs
                        document.getElementById('auto-processed').textContent = s.stats.processed || 0;
                        document.getElementById('auto-pending').textContent = s.queue || 0;
                        document.getElementById('auto-errors').textContent = s.stats.errors || 0;
                        document.getElementById('auto-running').textContent = s.running ? '▶️' : '⏸️';
                        
                        // Panel
                        document.getElementById('auto-status').innerHTML = 
                            '<p><strong>Estado:</strong> ' + (s.running ? '🟢 ACTIVO' : '🔴 DETENIDO') + '</p>' +
                            '<p><strong>Carpeta:</strong> ' + s.watch_dir + '</p>' +
                            '<p><strong>Procesados:</strong> ' + (s.stats.processed||0) + '</p>' +
                            '<p><strong>En Cola:</strong> ' + (s.queue||0) + '</p>';
                        
                        // Cola
                        var queueHTML = '<p style="color:#999;text-align:center;padding:40px">✅ No hay archivos</p>';
                        if (s.queue_items && s.queue_items.length > 0) {
                            queueHTML = s.queue_items.map(function(item) {
                                return '<div style="padding:10px;border-bottom:1px solid #eee">' + 
                                       '<strong>' + item.file.split('/').pop() + '</strong>' +
                                       '<span style="float:right;color:#999">' + item.status + '</span>' +
                                       '</div>';
                            }).join('');
                        }
                        document.getElementById('processing-queue').innerHTML = queueHTML;
                        
                        console.log('✅ Status actualizado');
                    }
                })
                .catch(function(error) {
                    console.error('❌ Error:', error);
                    document.getElementById('auto-status').innerHTML = 
                        '<p style="color:#dc3545">❌ Error: ' + error.message + '</p>';
                });
        }
        
        function startAutoProcessor() {
            fetch('/api/autoprocessor/start', {method:'POST'})
                .then(function(r) { return r.json(); })
                .then(function(d) { 
                    alert(d.message); 
                    loadAutoProcessorStatus(); 
                })
                .catch(function(e) { alert('Error: ' + e.message); });
        }
        
        function stopAutoProcessor() {
            fetch('/api/autoprocessor/stop', {method:'POST'})
                .then(function(r) { return r.json(); })
                .then(function(d) { 
                    alert(d.message); 
                    loadAutoProcessorStatus(); 
                })
                .catch(function(e) { alert('Error: ' + e.message); });
        }
        
        function scanFiles() {
            if (!confirm('¿Escanear archivos en PENDIENTES?')) return;
            
            fetch('/api/autoprocessor/scan', {method:'POST'})
                .then(function(r) { return r.json(); })
                .then(function(d) { 
                    alert(d.message); 
                    loadAutoProcessorStatus(); 
                })
                .catch(function(e) { alert('Error: ' + e.message); });
        }
        
        // Auto-actualizar cada 5 segundos si el tab está activo
        setInterval(function() {
            var section = document.getElementById('autoprocesos');
            if (section && section.classList.contains('active')) {
                loadAutoProcessorStatus();
            }
        }, 5000);
'''

# PASO 3: Insertar antes del ÚLTIMO </script> antes de </body>
contenido_nuevo = ''.join(nuevas_lineas)

# Buscar el último </script> antes de </body>
partes = contenido_nuevo.rsplit('</script>', 1)
if len(partes) == 2:
    contenido_final = partes[0] + js_limpio + '\n    </script>' + partes[1]
else:
    contenido_final = contenido_nuevo + js_limpio

# Guardar
with open('templates/index.html', 'w', encoding='utf-8') as f:
    f.write(contenido_final)

print("")
print("✅ Limpieza completada")
print("   - Funciones duplicadas eliminadas")
print("   - Una única versión funcional")
print("   - JavaScript ES5 compatible")

