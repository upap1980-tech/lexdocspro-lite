#!/usr/bin/env python3
"""
Parchar run.py mega para compatibilidad con tu proyecto
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# 1. PROBLEMA: Líneas con "ai_agent" que no existe en tu proyecto
# Buscar estas líneas:
#   doc_generator = DocumentGenerator(ai_service, ai_agent)
#   lexnet_service = LexNetNotifications(db_manager=db, ai_agent=ai_agent)

# SOLUCIÓN: Comentar o quitar ai_agent

# Reemplazar líneas problemáticas
contenido = contenido.replace(
    'doc_generator = DocumentGenerator(ai_service, ai_agent)',
    'doc_generator = DocumentGenerator(ai_service)'
)

contenido = contenido.replace(
    'lexnet_service = LexNetNotifications(db_manager=db, ai_agent=ai_agent)',
    'lexnet_service = LexNetNotifications(db_manager=db)'
)

# 2. PROBLEMA: Comentarios extraños "Módulo desactivado en versión LITE"
# Ya están en el código, no hacer nada

# 3. PROBLEMA: Imports que pueden faltar
# Añadir try-except en imports opcionales

# Buscar el bloque de imports de servicios opcionales y protegerlos
imports_opcionales = '''
# Servicios opcionales (pueden no estar implementados)
try:
    from services.db_service import DatabaseService
    from services.decision_engine import DecisionEngine
    db_service = DatabaseService()
    decision_engine = DecisionEngine()
except ImportError as e:
    print(f"⚠️  Servicios opcionales no disponibles: {e}")
    db_service = None
    decision_engine = None
'''

# No modificamos esto ahora, solo advertimos

# 4. AJUSTAR paths de base de datos si usa models.py
# El código usa "db = DatabaseManager()" pero tu proyecto tiene models.py
# Vamos a unificar

contenido = contenido.replace(
    'from models import DatabaseManager\ndb = DatabaseManager()',
    '''# Importar DatabaseManager o usar el existente
try:
    from models import DatabaseManager
    db = DatabaseManager()
except ImportError:
    try:
        from models import db
    except ImportError:
        print("⚠️  No se pudo importar DatabaseManager ni db de models.py")
        db = None'''
)

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ run.py parcheado exitosamente")
print("")
print("🔍 Verificaciones necesarias:")
print("   1. Verificar que models.py existe")
print("   2. Verificar que decorators.py existe")
print("   3. Verificar que services/db_service.py existe")
print("   4. Verificar que services/decision_engine.py existe")
print("")
print("Si alguno falta, crear stubs básicos")

