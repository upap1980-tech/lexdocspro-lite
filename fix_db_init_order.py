#!/usr/bin/env python3
"""
Fix: Mover inicialización de DatabaseManager después de crear app
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# PASO 1: Eliminar la línea problemática (línea ~99)
contenido = contenido.replace(
    '''# Inicializar Base de Datos para servicios (Models v3.0)
from models import DatabaseManager
db = DatabaseManager()

# Módulo desactivado en versión LITE
# Módulo desactivado en versión LITE
# Módulo desactivado en versión LITE

doc_generator = DocumentGenerator(ai_service, ai_agent)''',
    '''# Inicializar Base de Datos para servicios (Models v3.0)
# NOTA: db se inicializa DESPUÉS de crear app (línea ~50)

# Módulo desactivado en versión LITE
# Módulo desactivado en versión LITE
# Módulo desactivado en versión LITE

# doc_generator se inicializa después de db
doc_generator = None  # Temporal'''
)

# PASO 2: Añadir inicialización correcta DESPUÉS de JWT
contenido = contenido.replace(
    '''# Inicializar JWT
jwt = JWTManager(app)

# Servicios existentes
from services.ocr_service import OCRService''',
    '''# Inicializar JWT
jwt = JWTManager(app)

# ═══════════════════════════════════════════════════════════════
# INICIALIZAR DATABASE MANAGER (necesita app creada primero)
# ═══════════════════════════════════════════════════════════════
from models import DatabaseManager
db = DatabaseManager(app)
print(f"🗄️  DatabaseManager inicializado: {DB_PATH}")

# ═══════════════════════════════════════════════════════════════
# SERVICIOS (ahora que db está listo)
# ═══════════════════════════════════════════════════════════════
from services.ocr_service import OCRService''')

# PASO 3: Inicializar doc_generator DESPUÉS de db
contenido = contenido.replace(
    '''# doc_generator se inicializa después de db
doc_generator = None  # Temporal
lexnet_analyzer = LexNetAnalyzer(ai_service)''',
    '''# doc_generator se inicializa después de tener db
doc_generator = DocumentGenerator(ai_service)
lexnet_analyzer = LexNetAnalyzer(ai_service)''')

# PASO 4: Eliminar imports duplicados de DatabaseManager
lineas = contenido.split('\n')
nueva_lineas = []
ya_importo_db_manager = False

for linea in lineas:
    if 'from models import DatabaseManager' in linea:
        if not ya_importo_db_manager:
            nueva_lineas.append(linea)
            ya_importo_db_manager = True
        # Si ya importó, saltar esta línea
    else:
        nueva_lineas.append(linea)

contenido = '\n'.join(nueva_lineas)

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Fix aplicado correctamente")
print("")
print("📋 Cambios realizados:")
print("   1. ✅ Eliminada inicialización prematura de DatabaseManager")
print("   2. ✅ Movida después de crear app Flask")
print("   3. ✅ Ajustado doc_generator para no usar ai_agent")
print("   4. ✅ Eliminados imports duplicados")
print("")
print("🚀 Ahora ejecuta: python run.py")

