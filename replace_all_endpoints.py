#!/usr/bin/env python3
"""
Reemplazar TODOS los endpoints de autoprocessor con versión funcional
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Buscar línea donde empiezan los endpoints de autoprocessor
start_idx = None
end_idx = None

for i, linea in enumerate(lineas):
    if '/api/autoprocessor/start' in linea and start_idx is None:
        # Buscar el @app.route anterior
        for j in range(i, max(0, i-5), -1):
            if '@app.route' in lineas[j]:
                start_idx = j
                break
    
    if start_idx is not None and end_idx is None:
        # Buscar el siguiente grupo de endpoints o el if __name__
        if i > start_idx + 10:
            if "if __name__ == '__main__':" in linea or \
               ('@app.route' in linea and '/api/autoprocessor' not in linea):
                end_idx = i
                break

if start_idx is not None and end_idx is not None:
    print(f"✅ Encontrados endpoints en líneas {start_idx+1} a {end_idx+1}")
    
    # Nuevos endpoints COMPLETOS
    nuevos_endpoints = '''
# ═══════════════════════════════════════════════════════════════
# AUTO-PROCESSOR ENDPOINTS (v3.2 - FIXED FINAL)
# ═══════════════════════════════════════════════════════════════

@app.route('/api/autoprocessor/status', methods=['GET'])
def autoprocessor_status():
    """Obtener estado del auto-procesador"""
    try:
        status = autoprocessor.get_status()
        return jsonify({'success': True, 'status': status}), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/start', methods=['POST'])
def autoprocessor_start():
    """Iniciar el auto-procesador"""
    try:
        result = autoprocessor.start()
        return jsonify({
            'success': True,
            'message': '✅ Iniciado' if result else '⚠️ Ya estaba iniciado'
        }), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/stop', methods=['POST'])
def autoprocessor_stop():
    """Detener el auto-procesador"""
    try:
        result = autoprocessor.stop()
        return jsonify({
            'success': True,
            'message': '🛑 Detenido' if result else '⚠️ Ya estaba detenido'
        }), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/scan', methods=['POST'])
def autoprocessor_scan():
    """Escanear y procesar archivos"""
    try:
        files = autoprocessor.scan_existing_files()
        
        if not files:
            return jsonify({
                'success': True,
                'processed': 0,
                'message': '✅ No hay archivos'
            }), 200
        
        import threading
        for f in files:
            threading.Thread(target=autoprocessor.process_file, args=(f,), daemon=True).start()
        
        return jsonify({
            'success': True,
            'processed': len(files),
            'message': f'✅ {len(files)} archivo(s) en proceso'
        }), 200
    except Exception as e:
        print(f"❌ Error: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

'''
    
    # Reemplazar
    nuevas_lineas = lineas[:start_idx] + [nuevos_endpoints] + lineas[end_idx:]
    
    # Guardar
    with open('run.py', 'w', encoding='utf-8') as f:
        f.writelines(nuevas_lineas)
    
    print("✅ Endpoints reemplazados (versión ultra-simple)")
else:
    print("❌ No se encontraron los endpoints")

