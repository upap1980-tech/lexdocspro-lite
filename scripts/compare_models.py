#!/usr/bin/env python3
"""Comparar modelos instalados para derecho español"""
import time
from services.ollamaservice import OllamaService

PROMPT_TEST = """Analiza el siguiente caso:

Un arrendador quiere desahuciar a un inquilino por impago de 3 meses de renta. 
El contrato es verbal, sin depósito. ¿Qué procedimiento debe seguir?

Responde citando normativa aplicable."""

def test_model(model_name):
    print(f"\n{'='*70}")
    print(f"🤖 Probando: {model_name}")
    print('='*70)
    
    service = OllamaService()
    service.model = model_name
    
    start = time.time()
    try:
        response = service.chat(PROMPT_TEST)
        elapsed = time.time() - start
        
        print(f"⏱️  Tiempo: {elapsed:.2f}s")
        print(f"📝 Longitud: {len(response)} caracteres")
        print(f"\n📄 Respuesta:\n")
        print(response[:500] + "..." if len(response) > 500 else response)
        
        return {
            'model': model_name,
            'time': elapsed,
            'length': len(response),
            'success': True
        }
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'model': model_name, 'success': False}

# Modelos a probar
models = [
    "lexdocs-legal",
    "lexdocs-llama3",  # El nuevo que vamos a crear
    "mistral",
    "llama3"
]

results = []
for model in models:
    result = test_model(model)
    results.append(result)
    time.sleep(2)  # Pausa entre consultas

# Resumen
print(f"\n\n{'='*70}")
print("📊 RESUMEN COMPARATIVO")
print('='*70)
for r in results:
    if r['success']:
        print(f"✅ {r['model']:20} | {r['time']:6.2f}s | {r['length']:5} chars")
    else:
        print(f"❌ {r['model']:20} | ERROR")
