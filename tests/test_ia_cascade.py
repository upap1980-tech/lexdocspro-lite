#!/usr/bin/env python3
"""
TEST SUITE PARA IA CASCADE SERVICE v3.0
Valida funcionamiento de todos los providers
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.ia_cascade_service import ia_cascade
import time


class TestIACascade:
    def __init__(self):
        self.passed = 0
        self.failed = 0
        self.tests = []
    
    def run_test(self, name, test_func):
        """Ejecutar un test individual"""
        print(f"\n{'='*70}")
        print(f"🧪 TEST: {name}")
        print(f"{'='*70}")
        
        try:
            result = test_func()
            if result:
                self.passed += 1
                self.tests.append({'name': name, 'status': 'PASSED', 'error': None})
                print(f"✅ PASSED: {name}")
            else:
                self.failed += 1
                self.tests.append({'name': name, 'status': 'FAILED', 'error': 'Test returned False'})
                print(f"❌ FAILED: {name}")
        except Exception as e:
            self.failed += 1
            self.tests.append({'name': name, 'status': 'FAILED', 'error': str(e)})
            print(f"❌ FAILED: {name}")
            print(f"   Error: {e}")
    
    def print_summary(self):
        """Imprimir resumen de tests"""
        total = self.passed + self.failed
        success_rate = (self.passed / total * 100) if total > 0 else 0
        
        print(f"\n{'='*70}")
        print(f"📊 RESUMEN DE TESTS")
        print(f"{'='*70}")
        print(f"Total: {total}")
        print(f"✅ Passed: {self.passed}")
        print(f"❌ Failed: {self.failed}")
        print(f"📈 Success Rate: {success_rate:.2f}%")
        print(f"{'='*70}\n")
        
        if self.failed > 0:
            print("❌ TESTS FALLIDOS:")
            for test in self.tests:
                if test['status'] == 'FAILED':
                    print(f"  - {test['name']}: {test['error']}")
            print()


# ========== TESTS ==========

def test_service_initialization():
    """Test: Servicio se inicializa correctamente"""
    assert ia_cascade is not None, "Servicio no inicializado"
    assert ia_cascade.providers_config is not None, "Configuración de providers no cargada"
    assert len(ia_cascade.providers_config) == 7, f"Se esperan 7 providers, encontrados {len(ia_cascade.providers_config)}"
    return True


def test_get_stats():
    """Test: Obtener estadísticas funciona"""
    stats = ia_cascade.get_stats()
    assert 'providers' in stats, "Falta 'providers' en stats"
    assert 'global' in stats, "Falta 'global' en stats"
    assert 'total_calls' in stats['global'], "Falta 'total_calls' en stats globales"
    print(f"  Stats obtenidas correctamente: {stats['global']['total_calls']} llamadas totales")
    return True


def test_get_providers_config():
    """Test: Obtener configuración de providers"""
    config = ia_cascade.get_all_providers_config()
    assert len(config) == 7, f"Se esperan 7 providers, encontrados {len(config)}"
    
    required_fields = ['name', 'model', 'enabled', 'local', 'priority', 'has_api_key']
    for provider_id, provider_config in config.items():
        for field in required_fields:
            assert field in provider_config, f"Falta campo '{field}' en {provider_id}"
    
    print(f"  Configuración de {len(config)} providers validada")
    return True


def test_ollama_local():
    """Test: Ollama local (si está disponible)"""
    config = ia_cascade.get_provider_config('ollama')
    if not config or not config['enabled']:
        print("  ⏭️ SKIP: Ollama no habilitado")
        return True
    
    result = ia_cascade.consultar_cascade(
        "Responde con una sola palabra: OK",
        temperature=0.1,
        force_provider='ollama'
    )
    
    if result.get('success'):
        print(f"  ✅ Ollama respondió en {result.get('time', 0):.2f}s")
        print(f"  📄 Respuesta: {result.get('response', '')[:100]}...")
        return True
    else:
        print(f"  ⚠️ Ollama no disponible (normal si no está corriendo)")
        print(f"  Error: {result.get('error')}")
        return True  # No fallar el test si Ollama no está corriendo


def test_groq_cloud():
    """Test: Groq Cloud (si está configurado)"""
    config = ia_cascade.get_provider_config('groq')
    if not config or not config['enabled']:
        print("  ⏭️ SKIP: Groq no configurado")
        return True
    
    result = ia_cascade.consultar_cascade(
        "Responde con una sola palabra: OK",
        temperature=0.1,
        force_provider='groq'
    )
    
    if result.get('success'):
        print(f"  ✅ Groq respondió en {result.get('time', 0):.2f}s")
        print(f"  📄 Respuesta: {result.get('response', '')[:100]}...")
        print(f"  📊 Tokens: {result.get('metadata', {}).get('tokens', 'N/A')}")
        return True
    else:
        print(f"  ❌ Groq falló: {result.get('error')}")
        return False


def test_cascade_fallback():
    """Test: Cascade automático con fallback"""
    result = ia_cascade.consultar_cascade(
        "¿Qué es el artículo 133 de la LEC? Responde en máximo 100 palabras.",
        temperature=0.3
    )
    
    assert result is not None, "Resultado es None"
    
    if result.get('success'):
        print(f"  ✅ Cascade exitoso con {result.get('provider_used')}")
        print(f"  ⏱️ Tiempo: {result.get('time', 0):.2f}s")
        print(f"  📄 Respuesta ({len(result.get('response', ''))} chars): {result.get('response', '')[:200]}...")
        return True
    else:
        print(f"  ❌ Cascade falló: {result.get('error')}")
        print(f"  Intentos realizados: {result.get('metadata', {}).get('attempts', 'N/A')}")
        return False


def test_analyze_document():
    """Test: Análisis de documento legal"""
    sample_text = """
    AUTO DEL JUZGADO DE PRIMERA INSTANCIA Nº 5 DE MADRID
    
    PROCEDIMIENTO: Juicio Ordinario 123/2024
    DEMANDANTE: Juan Pérez García
    DEMANDADO: María López Rodríguez
    
    MADRID, 15 de enero de 2026
    
    Se acuerda admitir a trámite la demanda...
    """
    
    result = ia_cascade.analyze_document(sample_text)
    
    if result.get('success'):
        metadata = result.get('metadata', {})
        print(f"  ✅ Documento analizado correctamente")
        print(f"  📋 Tipo: {metadata.get('tipo_documento', 'N/A')}")
        print(f"  👤 Cliente: {metadata.get('nombre_cliente', 'N/A')}")
        print(f"  📅 Fecha: {metadata.get('fecha_documento', 'N/A')}")
        print(f"  ⚖️ Juzgado: {metadata.get('juzgado', 'N/A')}")
        
        # Validar que extrajo algo
        assert metadata.get('tipo_documento'), "No se extrajo tipo de documento"
        return True
    else:
        print(f"  ❌ Análisis falló: {result.get('error')}")
        return False


def test_toggle_provider():
    """Test: Habilitar/deshabilitar provider"""
    # Deshabilitar Groq temporalmente
    success1 = ia_cascade.toggle_provider('groq', False)
    assert success1, "No se pudo deshabilitar Groq"
    
    config1 = ia_cascade.get_provider_config('groq')
    assert not config1['enabled'], "Groq no se deshabilitó"
    
    print("  ✅ Provider deshabilitado correctamente")
    
    # Volver a habilitar
    success2 = ia_cascade.toggle_provider('groq', True)
    assert success2, "No se pudo habilitar Groq"
    
    config2 = ia_cascade.get_provider_config('groq')
    assert config2['enabled'], "Groq no se habilitó"
    
    print("  ✅ Provider habilitado correctamente")
    
    return True


def test_stats_persistence():
    """Test: Persistencia de estadísticas"""
    # Forzar guardado
    ia_cascade._save_stats()
    
    # Verificar que se creó el archivo
    import os
    stats_file = os.path.join(os.path.dirname(__file__), '..', 'ia_cascade_stats.json')
    assert os.path.exists(stats_file), "Archivo de stats no creado"
    
    print(f"  ✅ Stats guardadas en: {stats_file}")
    
    # Verificar que se puede leer
    import json
    with open(stats_file, 'r') as f:
        stats_data = json.load(f)
    
    assert len(stats_data) > 0, "Stats vacías"
    print(f"  ✅ Stats cargadas correctamente ({len(stats_data)} providers)")
    
    return True


# ========== EJECUTAR TESTS ==========

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("🚀 IA CASCADE SERVICE - TEST SUITE v3.0")
    print("=" * 70)
    
    tester = TestIACascade()
    
    # Ejecutar tests
    tester.run_test("Inicialización del servicio", test_service_initialization)
    tester.run_test("Obtener estadísticas", test_get_stats)
    tester.run_test("Obtener configuración de providers", test_get_providers_config)
    tester.run_test("Test Ollama local", test_ollama_local)
    tester.run_test("Test Groq Cloud", test_groq_cloud)
    tester.run_test("Test Cascade con fallback automático", test_cascade_fallback)
    tester.run_test("Test análisis de documento legal", test_analyze_document)
    tester.run_test("Test toggle provider", test_toggle_provider)
    tester.run_test("Test persistencia de stats", test_stats_persistence)
    
    # Resumen
    tester.print_summary()
    
    # Exit code
    sys.exit(0 if tester.failed == 0 else 1)
