#!/usr/bin/env python3
"""Comparar modelos Ollama directamente"""
import requests
import time
import json

OLLAMA_URL = "http://localhost:11434"

PROMPT = "¿Qué requisitos son necesarios para la validez de un contrato según el Código Civil español? Indica los artículos aplicables."

def test_model(model_name):
    print(f"\n{'='*70}")
    print(f"🤖 Probando: {model_name}")
    print('='*70)
    
    start = time.time()
    try:
        response = requests.post(
            f"{OLLAMA_URL}/api/generate",
            json={
                "model": model_name,
                "prompt": PROMPT,
                "stream": False,
                "options": {
                    "temperature": 0.2,
                    "num_ctx": 8192
                }
            },
            timeout=90
        )
        
        elapsed = time.time() - start
        
        if response.status_code == 200:
            result = response.json().get('response', 'Sin respuesta')
            
            print(f"\n⏱️  Tiempo: {elapsed:.2f}s")
            print(f"📝 Longitud: {len(result)} caracteres")
            print(f"\n📄 Respuesta:\n")
            print(result[:700] + "..." if len(result) > 700 else result)
            
            return {
                'model': model_name,
                'time': elapsed,
                'length': len(result),
                'success': True
            }
        else:
            print(f"❌ Error HTTP {response.status_code}")
            return {'model': model_name, 'success': False}
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'model': model_name, 'success': False}

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
    results.append(result)
    time.sleep(2)

# RESUMEN
print(f"\n\n{'='*70}")
print("📊 RESUMEN COMPARATIVO")
print('='*70)
print(f"{'Modelo':<25} {'Tiempo':>10} {'Longitud':>12} {'Estado':>10}")
print('-'*70)

for r in results:
    if r['success']:
        print(f"{r['model']:<25} {r['time']:>9.2f}s {r['length']:>12} {'✅ OK':>10}")
    else:
        print(f"{r['model']:<25} {'-':>10} {'-':>12} {'❌ Error':>10}")

print("\n💡 Mejor modelo: El más rápido con respuestas completas y precisas")
