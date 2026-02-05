#!/usr/bin/env python3
"""
Script para reemplazar endpoints de IA CASCADE en run.py
"""

import re
import shutil
from datetime import datetime

def fix_ia_cascade_endpoints():
    run_py_path = 'run.py'
    
    # Backup
    backup_path = f'run.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy(run_py_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Leer archivo
    with open(run_py_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Buscar sección de IA CASCADE endpoints antiguos
    # Desde "# IA CASCADE ENDPOINTS" hasta "def autoprocessor_log"
    
    pattern = r"# ═+\s*# IA CASCADE ENDPOINTS.*?(?=def autoprocessor_log)"
    
    # Nuevo código
    new_code = '''# ═══════════════════════════════════════════════════════════════
# IA CASCADE ENDPOINTS v3.0
# ═══════════════════════════════════════════════════════════════

@app.route('/api/ia-cascade/stats', methods=['GET'])
@jwt_required()
def ia_cascade_stats():
    """
    Obtener estadísticas de todos los providers
    
    Returns:
        JSON con stats globales y por provider
    """
    try:
        stats = ia_cascade.get_stats()
        return jsonify({
            'success': True,
            'stats': stats
        }), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/providers', methods=['GET'])
@jwt_required()
def ia_cascade_providers():
    """
    Obtener configuración de todos los providers (sin API keys)
    
    Returns:
        JSON con nombre, modelo, estado, prioridad de cada provider
    """
    try:
        providers = ia_cascade.get_all_providers_config()
        return jsonify({
            'success': True,
            'providers': providers
        }), 200
    except Exception as e:
        print(f"❌ Error en ia_cascade_providers: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/test', methods=['POST'])
@jwt_required()
def ia_cascade_test():
    """
    Testar un provider específico o cascade automático
    
    Body JSON:
        - prompt: str (requerido)
        - provider: str (opcional, default 'cascade')
        - temperature: float (opcional, default 0.3)
        - max_tokens: int (opcional, default 2000)
    
    Returns:
        JSON con respuesta, provider usado, tiempo, metadata
    """
    try:
        data = request.json
        prompt = data.get('prompt', '¿Qué es el artículo 133 de la LEC?')
        provider = data.get('provider', 'cascade')
        temperature = data.get('temperature', 0.3)
        max_tokens = data.get('max_tokens', 2000)
        
        print(f"🧪 Test IA Cascade: provider={provider}, temp={temperature}")
        
        if provider == 'cascade':
            result = ia_cascade.consultar_cascade(prompt, temperature, max_tokens)
        else:
            result = ia_cascade.consultar_cascade(prompt, temperature, max_tokens, force_provider=provider)
        
        return jsonify({
            'success': result.get('success'),
            'response': result.get('response'),
            'provider_used': result.get('provider_used'),
            'time': result.get('time'),
            'metadata': result.get('metadata', {}),
            'error': result.get('error')
        }), 200
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_test: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/update-key', methods=['POST'])
@jwt_required()
def ia_cascade_update_key():
    """
    Actualizar API key de un provider
    
    Body JSON:
        - provider_id: str (requerido)
        - api_key: str (requerido)
    """
    try:
        data = request.json
        provider_id = data.get('provider_id')
        api_key = data.get('api_key')
        
        if not provider_id or not api_key:
            return jsonify({
                'success': False,
                'error': 'Faltan parámetros: provider_id y api_key son requeridos'
            }), 400
        
        success = ia_cascade.update_api_key(provider_id, api_key)
        
        if success:
            print(f"✅ API key de {provider_id} actualizada")
            return jsonify({
                'success': True,
                'message': f'✅ API key de {provider_id} actualizada correctamente'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_id} no encontrado'
            }), 404
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_update_key: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/toggle-provider', methods=['POST'])
@jwt_required()
def ia_cascade_toggle_provider():
    """
    Habilitar/deshabilitar un provider
    
    Body JSON:
        - provider_id: str (requerido)
        - enabled: bool (requerido)
    """
    try:
        data = request.json
        provider_id = data.get('provider_id')
        enabled = data.get('enabled', False)
        
        if not provider_id:
            return jsonify({
                'success': False,
                'error': 'Falta parámetro: provider_id es requerido'
            }), 400
        
        success = ia_cascade.toggle_provider(provider_id, enabled)
        
        if success:
            status = '✅ habilitado' if enabled else '⏸️ deshabilitado'
            print(f"{status}: {provider_id}")
            return jsonify({
                'success': True,
                'message': f'Provider {provider_id} {status}'
            }), 200
        else:
            return jsonify({
                'success': False,
                'error': f'Provider {provider_id} no encontrado'
            }), 404
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_toggle_provider: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/ia-cascade/reset-stats', methods=['POST'])
@jwt_required()
def ia_cascade_reset_stats():
    """
    Resetear estadísticas de un provider o todos
    
    Body JSON (opcional):
        - provider_id: str (opcional, si se omite resetea todos)
    """
    try:
        data = request.json or {}
        provider_id = data.get('provider_id')
        
        ia_cascade.reset_stats(provider_id)
        
        if provider_id:
            print(f"🗑️ Stats reseteadas para {provider_id}")
            message = f'Stats reseteadas para {provider_id}'
        else:
            print(f"🗑️ Stats reseteadas globalmente")
            message = 'Stats reseteadas globalmente'
        
        return jsonify({
            'success': True,
            'message': message
        }), 200
    
    except Exception as e:
        print(f"❌ Error en ia_cascade_reset_stats: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


# ═══════════════════════════════════════════════════════════════
# AUTO-PROCESSOR ENDPOINTS (HEREDADOS - MANTENER)
# ═══════════════════════════════════════════════════════════════

'''
    
    # Reemplazar
    new_content = re.sub(pattern, new_code, content, flags=re.DOTALL)
    
    # Guardar
    with open(run_py_path, 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✅ Endpoints de IA CASCADE actualizados en run.py")
    print("")
    print("📋 Cambios realizados:")
    print("  - /api/ia-cascade/stats → Nuevo")
    print("  - /api/ia-cascade/providers → Nuevo")
    print("  - /api/ia-cascade/test → Actualizado")
    print("  - /api/ia-cascade/update-key → Nuevo")
    print("  - /api/ia-cascade/toggle-provider → Actualizado")
    print("  - /api/ia-cascade/reset-stats → Nuevo")
    print("")
    print("✅ Endpoints de autoprocessor mantenidos sin cambios")

if __name__ == '__main__':
    fix_ia_cascade_endpoints()
