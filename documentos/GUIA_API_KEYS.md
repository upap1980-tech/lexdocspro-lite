# 🔑 Guía para Obtener API Keys

## ⚡ Groq (RECOMENDADO - Gratis y Ultra Rápido)

**Ventajas:**
- ✅ **GRATIS** con generoso límite
- ✅ Extremadamente rápido (hasta 10x más que OpenAI)
- ✅ Modelos potentes (Llama 3.1 70B)
- ✅ Sin tarjeta de crédito requerida

**Pasos:**
1. Ve a: https://console.groq.com
2. Crea cuenta con Google/GitHub
3. Navega a "API Keys": https://console.groq.com/keys
4. Click "Create API Key"
5. Copia la clave (empieza con `gsk_`)
6. Añádela al `.env`:

GROQ_API_KEY=gsk_tu_clave_aqui

**Modelos disponibles:**
- `llama-3.1-70b-versatile` - Más potente
- `llama-3.1-8b-instant` - Más rápido
- `mixtral-8x7b-32768` - Excelente para español

---

## 🤖 OpenAI (ChatGPT)

**Ventajas:**
- Modelos muy potentes (GPT-4)
- Excelente para español

**Desventajas:**
- 💰 De pago (~$0.01/1K tokens)
- Requiere tarjeta de crédito

**Pasos:**
1. Ve a: https://platform.openai.com/api-keys
2. Crea cuenta
3. Añade método de pago
4. Crea API Key
5. Añádela al `.env`:

OPENAI_API_KEY=sk-proj-tu_clave_aqui



**Créditos:**
- Nueva cuenta: $5 gratis (3 meses)
- GPT-4 Turbo: ~$0.01 por consulta
- GPT-3.5 Turbo: ~$0.002 por consulta

---

## 🔍 Perplexity

**Ventajas:**
- Búsqueda en tiempo real
- Cita fuentes automáticamente

**Pasos:**
1. Ve a: https://www.perplexity.ai/settings/api
2. Crea cuenta Pro ($20/mes incluye API)
3. Genera API Key
4. Añádela al `.env`:

PERPLEXITY_API_KEY=pplx-tu_clave_aqui

---

## 💎 Google Gemini

**Ventajas:**
- Gratis con límite generoso
- Bueno para multimodal

**Pasos:**
1. Ve a: https://makersuite.google.com/app/apikey
2. Crea API Key con cuenta Google
3. Añádela al `.env`:

GEMINI_API_KEY=tu_clave_aqui

**Límites gratis:**
- 60 consultas/minuto
- 1 millón tokens/mes

---

## 🌊 DeepSeek

**Ventajas:**
- Muy económico (~$0.001/1K tokens)
- Bueno para código

**Pasos:**
1. Ve a: https://platform.deepseek.com
2. Crea cuenta
3. Añade créditos ($5 mínimo)
4. Genera API Key en: https://platform.deepseek.com/api_keys
5. Añádela al `.env`:

DEEPSEEK_API_KEY=tu_clave_aqui

---

## 🏠 Ollama (Local - Sin API Key)

**Ventajas:**
- ✅ Completamente gratis
- ✅ Sin límites
- ✅ Privacidad total (datos locales)

**Ya configurado:**
- Modelo: `lexdocs-legal`
- Basado en Mistral 7B
- Optimizado para derecho español

---

## 🎯 Recomendación

**Para empezar:**
1. **Groq** (gratis, rápido) para consultas rápidas
2. **Ollama** (local) para privacidad
3. **OpenAI GPT-4** (pago) para análisis complejos

**Configuración ideal:**
```env
# Gratuitos
GROQ_API_KEY=gsk_...        # ⚡ Velocidad
GEMINI_API_KEY=...          # 💎 Alternativa gratis

# De pago (opcional)
OPENAI_API_KEY=sk-proj-...  # 🤖 Calidad máxima

💰 Comparación de Costos

| Proveedor    | Costo/1M tokens | Velocidad | Calidad |
| ------------ | --------------- | --------- | ------- |
| Groq         | GRATIS          | ⚡⚡⚡⚡⚡     | ⭐⭐⭐⭐    |
| Ollama       | GRATIS          | ⚡⚡⚡       | ⭐⭐⭐⭐    |
| Gemini       | GRATIS (límite) | ⚡⚡⚡       | ⭐⭐⭐     |
| DeepSeek     | $0.27           | ⚡⚡⚡       | ⭐⭐⭐     |
| OpenAI GPT-4 | $10.00          | ⚡⚡        | ⭐⭐⭐⭐⭐   |
| Perplexity   | $20/mes         | ⚡⚡⚡⚡      | ⭐⭐⭐⭐    |
| EOF          |                 |           |         |
echo "✅ Guía de API Keys creada"

### **6. Script de prueba para Groq**

```bash
cat > test_groq.py << 'EOF'
#!/usr/bin/env python3
"""
Probar Groq API
"""
import os
from dotenv import load_dotenv

load_dotenv()

def test_groq():
    groq_key = os.getenv('GROQ_API_KEY')
    
    if not groq_key:
        print("❌ GROQ_API_KEY no configurada")
        print("\n📝 Para obtener una API key GRATIS:")
        print("   1. Ve a: https://console.groq.com")
        print("   2. Crea cuenta")
        print("   3. Ve a API Keys: https://console.groq.com/keys")
        print("   4. Copia la key y añádela al archivo .env:")
        print("      GROQ_API_KEY=gsk_tu_clave_aqui")
        return
    
    print("🧪 Probando Groq API...")
    print(f"✅ API Key configurada: {groq_key[:20]}...")
    
    try:
        from groq import Groq
        client = Groq(api_key=groq_key)
        
        print("\n📤 Enviando consulta legal de prueba...")
        
        response = client.chat.completions.create(
            model="llama-3.1-70b-versatile",
            messages=[
                {
                    "role": "system",
                    "content": "Eres un experto en derecho español."
                },
                {
                    "role": "user",
                    "content": "¿Qué dice el artículo 1254 del Código Civil español?"
                }
            ],
            temperature=0.3,
            max_tokens=500
        )
        
        print("\n📥 Respuesta recibida:")
        print("-" * 60)
        print(response.choices[0].message.content)
        print("-" * 60)
        
        print(f"\n✅ Groq funcionando correctamente!")
        print(f"⚡ Tiempo de respuesta: ULTRA RÁPIDO")
        print(f"💰 Costo: GRATIS")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")

if __name__ == '__main__':
    test_groq()
