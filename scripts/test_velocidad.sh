#!/bin/bash
echo "🧪 TEST DE VELOCIDAD DE PROVEEDORES IA"
echo "======================================"

PROMPT="Resume en 20 palabras: Auto judicial de inhibición"

# Test Ollama
echo -e "\n🏠 OLLAMA LOCAL:"
time curl -s -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"$PROMPT\",\"provider\":\"ollama\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','')[:100])"

# Test Groq
echo -e "\n⚡ GROQ ULTRA RÁPIDO:"
time curl -s -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"$PROMPT\",\"provider\":\"groq\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','')[:100])"

# Test Perplexity
echo -e "\n🔍 PERPLEXITY:"
time curl -s -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d "{\"prompt\":\"$PROMPT\",\"provider\":\"perplexity\"}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('response','')[:100])"

echo -e "\n✅ Test completado"
