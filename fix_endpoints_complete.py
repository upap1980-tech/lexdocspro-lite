#!/usr/bin/env python3
"""
Reemplazar completamente el bloque de endpoints 1623-1680
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Código correcto para endpoints (líneas 1623-1680)
codigo_correcto = '''# ═══════════════════════════════════════════════════════════════
# AUTO-PROCESSOR ENDPOINTS (v3.2 - FIXED)
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

@app.route('/api/autoprocessor/reset', methods=['POST'])
def autoprocessor_reset():
    """Resetear estadísticas"""
    try:
        autoprocessor.stats = {
            'processed': 0,
            'errors': 0,
            'pending': 0,
            'last_processed': None,
            'start_time': autoprocessor.stats.get('start_time')
        }
        autoprocessor.processing_queue = []
        
        return jsonify({
            'success': True,
            'message': '✅ Estadísticas reseteadas'
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocessor/log', methods=['GET'])
def autoprocessor_log():
    """Obtener log de procesamiento con trazabilidad"""
    try:
        limit = request.args.get('limit', 50, type=int)
        log = autoprocessor.get_processing_log(limit)
        
        return jsonify({
            'success': True,
            'log': log,
            'total': len(log)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

'''

# Reemplazar líneas 1622-1679 (índices 1621-1678)
nuevas_lineas = lineas[:1622] + [codigo_correcto + '\n'] + lineas[1680:]

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.writelines(nuevas_lineas)

print("✅ Endpoints de AutoProcessor completamente reescritos")
print("   - Líneas 1623-1680 reemplazadas")
print("   - Todas las funciones correctamente estructuradas")
print("   - 6 endpoints: status, start, stop, scan, reset, log")

