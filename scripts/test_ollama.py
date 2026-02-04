#!/usr/bin/env python3
from services.ollama_service import OllamaService

def test_ollama():
    print("🧪 Probando Ollama con modelo jurídico...\n")
    
    service = OllamaService()
    
    # Verificar salud
    print("1️⃣ Verificando conexión...")
    if service.check_health():
        print("   ✅ Ollama está corriendo\n")
    else:
        print("   ❌ Ollama no está disponible\n")
        return
    
    # Listar modelos
    print("2️⃣ Modelos disponibles:")
    models = service.get_available_models()
    for model in models:
        mark = "👉" if "lexdocs" in model else "  "
        print(f"   {mark} {model}")
    
    # Consulta de prueba
    print("\n3️⃣ Consulta jurídica de prueba:")
    print("   Pregunta: ¿Qué dice el artículo 1254 del Código Civil español?\n")
    
    response = service.chat("¿Qué dice el artículo 1254 del Código Civil español sobre el contrato?")
    
    print("   📝 Respuesta:")
    print("   " + "-"*60)
    print(response)
    print("   " + "-"*60)
    
    print("\n✅ Prueba completada")

if __name__ == '__main__':
    test_ollama()
