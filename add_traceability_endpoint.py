#!/usr/bin/env python3
"""
Añadir endpoint de trazabilidad
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

endpoint_nuevo = '''

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

if '/api/autoprocessor/log' not in contenido:
    # Insertar después del endpoint reset
    contenido = contenido.replace(
        "def autoprocessor_reset():",
        endpoint_nuevo + "@app.route('/api/autoprocessor/reset', methods=['POST'])\ndef autoprocessor_reset():"
    )
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ Endpoint de trazabilidad añadido")
else:
    print("✅ Ya existe")

