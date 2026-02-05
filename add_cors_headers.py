#!/usr/bin/env python3
"""
Añadir headers CORS explícitos a todos los endpoints de autoprocessor
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar los endpoints y añadir make_response
import re

# Reemplazar cada endpoint con versión que usa make_response
endpoints_fixes = [
    # START
    (
        r'(@app\.route\(\'/api/autoprocessor/start\'.*?\n)(def autoprocessor_start.*?return jsonify\(\{.*?\}\), 200)',
        r'''\1def autoprocessor_start():
    """Iniciar el auto-procesador"""
    try:
        result = autoprocessor.start()
        
        response = make_response(jsonify({
            'success': True,
            'message': '✅ Auto-procesador iniciado' if result else '⚠️ Ya estaba iniciado',
            'running': autoprocessor.is_running
        }), 200)
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_start: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500'''
    ),
    
    # STOP
    (
        r'(@app\.route\(\'/api/autoprocessor/stop\'.*?\n)(def autoprocessor_stop.*?return jsonify\(\{.*?\}\), 200)',
        r'''\1def autoprocessor_stop():
    """Detener el auto-procesador"""
    try:
        result = autoprocessor.stop()
        
        response = make_response(jsonify({
            'success': True,
            'message': '🛑 Auto-procesador detenido' if result else '⚠️ Ya estaba detenido',
            'running': autoprocessor.is_running
        }), 200)
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_stop: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500'''
    ),
    
    # SCAN
    (
        r'(@app\.route\(\'/api/autoprocessor/scan\'.*?\n)(def autoprocessor_scan.*?return jsonify\(\{.*?\}\), 200)',
        r'''\1def autoprocessor_scan():
    """Escanear y procesar archivos existentes"""
    try:
        files = autoprocessor.scan_existing_files()
        
        if not files:
            response = make_response(jsonify({
                'success': True,
                'processed': 0,
                'files': [],
                'message': '✅ No hay archivos para procesar'
            }), 200)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        
        # Procesar cada archivo
        import threading
        for file_path in files:
            thread = threading.Thread(
                target=autoprocessor.process_file,
                args=(file_path,)
            )
            thread.daemon = True
            thread.start()
        
        response = make_response(jsonify({
            'success': True,
            'processed': len(files),
            'files': [str(f.name) for f in files],
            'message': f'✅ {len(files)} archivo(s) en proceso'
        }), 200)
        
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Credentials'] = 'true'
        return response
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_scan: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500'''
    )
]

# Aplicar fixes (esto es complejo, mejor lo hacemos manual)
print("⚠️  Este fix es complejo, mejor hacerlo manual")
print("")
print("SOLUCIÓN RÁPIDA:")
print("Añade al inicio de run.py después de los imports:")
print("")
print("from flask import make_response")

