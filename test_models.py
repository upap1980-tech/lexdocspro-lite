#!/usr/bin/env python3
"""Comparar modelos Ollama para derecho español"""
import time
from services.ollama_service import OllamaService

PROMPT_TEST = "¿Qué requisitos son necesarios para la validez de un contrato según el Código Civil español? Indica los artículos aplicables."

def test_model(model_name):
    print(f"\n{'='*70}")
    print(f"🤖 Probando: {model_name}")
    print('='*70)
    
    service = OllamaService()
    service.model = model_name
    
    # Verificar salud
    if not service.check_health():
        print("❌ Ollama no está disponible")
        return None
    
    start = time.time()
    try:
        response = service.chat(PROMPT_TEST)
        elapsed = time.time() - start
        
        print(f"\n⏱️  Tiempo: {elapsed:.2f}s")
        print(f"📝 Longitud: {len(response)} caracteres")
        print(f"\n📄 Respuesta:\n")
        print(response[:700] + "..." if len(response) > 700 else response)
        
        return {
            'model': model_name,
            'time': elapsed,
            'length': len(response),
            'success': True
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'model': model_name, 'success': False, 'error': str(e)}

# COMPARATIVA
print("🔍 COMPARATIVA DE MODELOS LEGALES")
print("="*70)

models = [
    "lexdocs-llama3",   # Nuevo optimizado
    "lexdocs-legal",    # Actual basado en Mistral
    "llama3"            # Base sin optimización
]

results = []
for model in models:
    result = test_model(model)
    if result:
        results.append(result)
    time.sleep(1)

# RESUMEN
print(f"\n\n{'='*70}")
print("📊 RESUMEN COMPARATIVO")
print('='*70)
print(f"{'Modelo':<25} {'Tiempo':>10} {'Longitud':>12}")
print('-'*70)

for r in results:
    if r['success']:
        print(f"{r['model']:<25} {r['time']:>9.2f}s {r['length']:>12}")
    else:
        print(f"{r['model']:<25} {'ERROR':>10}")

print("\n💡 Recomendación: Usa el modelo más rápido con respuestas completas")
