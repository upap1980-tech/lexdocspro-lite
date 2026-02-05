#!/usr/bin/env python3
"""
Añadir endpoints de auto-procesamiento a run.py
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar donde añadir los endpoints (antes del if __name__)
if 'def autoprocessor_status' not in contenido:
    
    endpoints_autoprocessor = '''

# ═══════════════════════════════════════════════════════════════
# AUTO-PROCESSOR ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/autoprocessor/status', methods=['GET'])
@jwt_required()
def autoprocessor_status():
    """Obtener estado del auto-procesador"""
    try:
        status = autoprocessor.get_status()
        return jsonify({
            'success': True,
            'status': status
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/autoprocessor/start', methods=['POST'])
@jwt_required()
def autoprocessor_start():
    """Iniciar el auto-procesador"""
    try:
        result = autoprocessor.start()
        return jsonify({
            'success': result,
            'message': 'Auto-procesador iniciado' if result else 'Ya estaba iniciado'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/autoprocessor/stop', methods=['POST'])
@jwt_required()
def autoprocessor_stop():
    """Detener el auto-procesador"""
    try:
        result = autoprocessor.stop()
        return jsonify({
            'success': result,
            'message': 'Auto-procesador detenido' if result else 'Ya estaba detenido'
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/autoprocessor/scan', methods=['POST'])
@jwt_required()
def autoprocessor_scan():
    """Escanear y procesar archivos existentes"""
    try:
        files = autoprocessor.scan_existing_files()
        
        # Procesar cada archivo
        for file_path in files:
            autoprocessor.process_file(file_path)
        
        return jsonify({
            'success': True,
            'processed': len(files),
            'files': [f.name for f in files]
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''
    
    # Insertar antes del if __name__
    if "if __name__ == '__main__':" in contenido:
        partes = contenido.rsplit("if __name__ == '__main__':", 1)
        contenido = partes[0] + endpoints_autoprocessor + "\n\nif __name__ == '__main__':" + partes[1]
    else:
        contenido += endpoints_autoprocessor
    
    # Guardar
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ Endpoints de auto-procesador añadidos a run.py")
else:
    print("✅ Endpoints ya existen")

