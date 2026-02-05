#!/usr/bin/env python3
"""
Añadir endpoint para resetear estadísticas
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Añadir endpoint de reset
if '/api/autoprocessor/reset' not in contenido:
    endpoint_reset = '''

@app.route('/api/autoprocessor/reset', methods=['POST'])
def autoprocessor_reset():
    """Resetear estadísticas del auto-procesador"""
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

'''
    
    # Insertar después de otros endpoints de autoprocessor
    if '/api/autoprocessor/scan' in contenido:
        contenido = contenido.replace(
            "def autoprocessor_scan():",
            endpoint_reset + "\n@app.route('/api/autoprocessor/scan', methods=['POST'])\ndef autoprocessor_scan():"
        )
        
        with open('run.py', 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print("✅ Endpoint /api/autoprocessor/reset añadido")
    else:
        print("⚠️  No se encontró ubicación para insertar")
else:
    print("✅ Endpoint ya existe")

