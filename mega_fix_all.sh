#!/bin/bash
echo "🔧 Aplicando todos los fixes..."

# Fix 1: Orden de DatabaseManager
python fix_db_init_order.py

# Fix 2: ai_agent
python fix_ai_agent.py

# Fix 3: Verificar imports de servicios opcionales
cat > fix_optional_services.py <<'EOFOPT'
with open('run.py', 'r') as f:
    contenido = f.read()

# Proteger imports opcionales
contenido = contenido.replace(
    '''from services.db_service import DatabaseService
from services.decision_engine import DecisionEngine

# Inicializar servicios
db_service = DatabaseService()
decision_engine = DecisionEngine()''',
    '''# Servicios opcionales
try:
    from services.db_service import DatabaseService
    from services.decision_engine import DecisionEngine
    db_service = DatabaseService()
    decision_engine = DecisionEngine()
    print("✅ Servicios opcionales cargados")
except ImportError as e:
    print(f"⚠️  Servicios opcionales no disponibles: {e}")
    db_service = None
    decision_engine = None''')

with open('run.py', 'w') as f:
    f.write(contenido)
print("✅ Imports opcionales protegidos")
EOFOPT

python fix_optional_services.py

echo ""
echo "✅ Todos los fixes aplicados"
echo "🚀 Iniciando servidor..."
echo ""

python run.py
