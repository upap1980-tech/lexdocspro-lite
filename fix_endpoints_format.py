#!/usr/bin/env python3
"""
Fix: Endpoints deben devolver el formato que espera el frontend
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar y reemplazar los endpoints
import re

# 1. Fix endpoint /status
old_status = r'@app\.route\(\'/api/autoprocessor/status\'[^@]*?(?=@app\.route|if __name__|# ═)'
new_status = '''@app.route('/api/autoprocessor/status', methods=['GET'])
def autoprocessor_status():
    """Obtener estado del auto-procesador"""
    try:
        status = autoprocessor.get_status()
        
        # Devolver en formato que espera el frontend
        return jsonify({
            'success': True,
            'status': status
        }), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_status: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''

contenido = re.sub(old_status, new_status, contenido, flags=re.DOTALL)

# 2. Fix endpoint /start
old_start = r'@app\.route\(\'/api/autoprocessor/start\'[^@]*?(?=@app\.route|if __name__|# ═)'
new_start = '''@app.route('/api/autoprocessor/start', methods=['POST'])
def autoprocessor_start():
    """Iniciar el auto-procesador"""
    try:
        result = autoprocessor.start()
        
        return jsonify({
            'success': True,
            'message': '✅ Auto-procesador iniciado' if result else '⚠️ Ya estaba iniciado',
            'running': autoprocessor.is_running
        }), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_start: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''

contenido = re.sub(old_start, new_start, contenido, flags=re.DOTALL)

# 3. Fix endpoint /stop
old_stop = r'@app\.route\(\'/api/autoprocessor/stop\'[^@]*?(?=@app\.route|if __name__|# ═)'
new_stop = '''@app.route('/api/autoprocessor/stop', methods=['POST'])
def autoprocessor_stop():
    """Detener el auto-procesador"""
    try:
        result = autoprocessor.stop()
        
        return jsonify({
            'success': True,
            'message': '🛑 Auto-procesador detenido' if result else '⚠️ Ya estaba detenido',
            'running': autoprocessor.is_running
        }), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_stop: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''

contenido = re.sub(old_stop, new_stop, contenido, flags=re.DOTALL)

# 4. Fix endpoint /scan
old_scan = r'@app\.route\(\'/api/autoprocessor/scan\'[^@]*?(?=@app\.route|if __name__|# ═)'
new_scan = '''@app.route('/api/autoprocessor/scan', methods=['POST'])
def autoprocessor_scan():
    """Escanear y procesar archivos existentes"""
    try:
        files = autoprocessor.scan_existing_files()
        
        if not files:
            return jsonify({
                'success': True,
                'processed': 0,
                'files': [],
                'message': '✅ No hay archivos para procesar'
            }), 200
        
        # Procesar cada archivo
        import threading
        for file_path in files:
            thread = threading.Thread(
                target=autoprocessor.process_file,
                args=(file_path,)
            )
            thread.daemon = True
            thread.start()
        
        return jsonify({
            'success': True,
            'processed': len(files),
            'files': [str(f.name) for f in files],
            'message': f'✅ {len(files)} archivo(s) en proceso'
        }), 200
        
    except Exception as e:
        import traceback
        print(f"❌ Error en autoprocessor_scan: {e}")
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

'''

contenido = re.sub(old_scan, new_scan, contenido, flags=re.DOTALL)

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Endpoints actualizados con formato correcto")

