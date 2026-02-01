#!/usr/bin/env python3
"""Comparativa final: lexdocs-legal vs lexdocs-legal-pro"""
import time
from services.ollama_service import OllamaService

# Consultas de prueba variadas
TESTS = [
    {
        'name': 'Consulta simple',
        'prompt': '¿Qué dice el art. 1544 CC sobre compraventa de cosa ajena?'
    },
    {
        'name': 'Análisis de plazo',
        'prompt': 'He recibido una demanda civil. ¿Cuántos días tengo para contestar? Cita el artículo aplicable.'
    },
    {
        'name': 'Caso práctico',
        'prompt': 'Un arrendador quiere desahuciar por impago de 2 meses. El contrato es verbal. ¿Qué debe hacer?'
    }
]

def test_model(model_name, prompt):
    service = OllamaService()
    service.model = model_name
    
    start = time.time()
    try:
        response = service.chat(prompt)
        elapsed = time.time() - start
        return {
            'success': True,
            'time': elapsed,
            'response': response,
            'length': len(response)
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

print("="*80)
print("🏆 COMPARATIVA FINAL: lexdocs-legal vs lexdocs-legal-pro")
print("="*80)

models = ['lexdocs-legal', 'lexdocs-legal-pro']
all_results = {m: [] for m in models}

for i, test in enumerate(TESTS, 1):
    print(f"\n{'='*80}")
    print(f"📝 TEST {i}/3: {test['name']}")
    print(f"Pregunta: {test['prompt']}")
    print('='*80)
    
    for model in models:
        print(f"\n🤖 {model}")
        print('-'*80)
        
        result = test_model(model, test['prompt'])
        
        if result['success']:
            print(f"⏱️  Tiempo: {result['time']:.2f}s")
            print(f"📏 Longitud: {result['length']} caracteres")
            print(f"\n📄 Respuesta:\n{result['response'][:400]}...")
            all_results[model].append(result['time'])
        else:
            print(f"❌ Error: {result.get('error')}")
        
        time.sleep(1)

# RESUMEN ESTADÍSTICO
print(f"\n\n{'='*80}")
print("📊 RESUMEN ESTADÍSTICO")
print('='*80)

for model in models:
    if all_results[model]:
        avg_time = sum(all_results[model]) / len(all_results[model])
        print(f"\n{model}:")
        print(f"  • Tiempo promedio: {avg_time:.2f}s")
        print(f"  • Tiempo mínimo: {min(all_results[model]):.2f}s")
        print(f"  • Tiempo máximo: {max(all_results[model]):.2f}s")

# GANADOR
print(f"\n{'='*80}")
legal_avg = sum(all_results['lexdocs-legal']) / len(all_results['lexdocs-legal'])
pro_avg = sum(all_results['lexdocs-legal-pro']) / len(all_results['lexdocs-legal-pro'])

if pro_avg < legal_avg:
    winner = 'lexdocs-legal-pro'
    diff = ((legal_avg - pro_avg) / legal_avg) * 100
    print(f"🥇 GANADOR: {winner}")
    print(f"   {diff:.1f}% más rápido que lexdocs-legal")
else:
    winner = 'lexdocs-legal'
    diff = ((pro_avg - legal_avg) / legal_avg) * 100
    print(f"🥇 GANADOR: {winner}")
    if diff > 0:
        print(f"   {diff:.1f}% más rápido que lexdocs-legal-pro")
    else:
        print(f"   Rendimiento similar")

print(f"\n💡 RECOMENDACIÓN: Configurar {winner} como modelo predeterminado")
print('='*80)
