#!/usr/bin/env python3
"""
Añadir endpoints de IA Cascade a run.py
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Añadir import
if 'from services.ia_cascade_service import IACascadeService' not in contenido:
    contenido = contenido.replace(
        'from services.autoprocessor_service import AutoProcessorService',
        'from services.autoprocessor_service import AutoProcessorService\ntry:\n    from services.ia_cascade_service import IACascadeService\nexcept ImportError:\n    IACascadeService = None'
    )

# Añadir inicialización
if 'ia_cascade = IACascadeService' not in contenido:
    init_code = '''
# IA Cascade Service
try:
    if IACascadeService:
        ia_cascade = IACascadeService()
        print("✅ IA Cascade inicializado")
    else:
        ia_cascade = None
except Exception as e:
    print(f"⚠️  Error inicializando IA Cascade: {e}")
    ia_cascade = None
'''
    
    # Insertar después de autoprocessor
    if 'autoprocessor = AutoProcessorService' in contenido:
        contenido = contenido.replace(
            'autoprocessor.start()',
            'autoprocessor.start()\n' + init_code
        )

# Añadir endpoints
endpoints = '''

# ═══════════════════════════════════════════════════════════════
# IA CASCADE ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@app.route('/api/ia-cascade/status', methods=['GET'])
def ia_cascade_status():
    """Estado de todos los providers IA"""
    try:
        if not ia_cascade:
            return jsonify({'success': False, 'error': 'IA Cascade no disponible'}), 500
        
        status = ia_cascade.get_status()
        return jsonify({'success': True, 'status': status}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ia-cascade/query', methods=['POST'])
def ia_cascade_query():
    """Ejecutar query con fallback automático"""
    try:
        if not ia_cascade:
            return jsonify({'success': False, 'error': 'IA Cascade no disponible'}), 500
        
        data = request.get_json()
        prompt = data.get('prompt', '')
        
        if not prompt:
            return jsonify({'success': False, 'error': 'Prompt requerido'}), 400
        
        result = ia_cascade.query(
            prompt=prompt,
            max_tokens=data.get('max_tokens', 2000),
            temperature=data.get('temperature', 0.7)
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/ia-cascade/toggle/<provider_name>', methods=['POST'])
def ia_cascade_toggle(provider_name):
    """Activar/desactivar provider"""
    try:
        if not ia_cascade:
            return jsonify({'success': False, 'error': 'IA Cascade no disponible'}), 500
        
        data = request.get_json() or {}
        enable = data.get('enable', True)
        
        result = ia_cascade.toggle_provider(provider_name, enable)
        
        return jsonify({
            'success': result,
            'message': f"{'✅ Activado' if enable else '🔴 Desactivado'}: {provider_name}"
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

'''

if '/api/ia-cascade/status' not in contenido:
    # Insertar después de endpoints de autoprocessor
    if '@app.route(\'/api/autoprocessor/reset' in contenido:
        contenido = contenido.replace(
            "def autoprocessor_reset():",
            endpoints + "\n@app.route('/api/autoprocessor/reset', methods=['POST'])\ndef autoprocessor_reset():"
        )
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ Endpoints de IA Cascade añadidos")
else:
    print("✅ Endpoints ya existen")

