#!/usr/bin/env python3
"""
Fix: Importar DB_PATH antes de usarlo
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar la línea problemática
contenido = contenido.replace(
    '''# ═══════════════════════════════════════════════════════════════
# INICIALIZAR DATABASE MANAGER (necesita app creada primero)
# ═══════════════════════════════════════════════════════════════
from models import DatabaseManager
db = DatabaseManager(app)
print(f"🗄️  DatabaseManager inicializado: {DB_PATH}")''',
    '''# ═══════════════════════════════════════════════════════════════
# INICIALIZAR DATABASE MANAGER (necesita app creada primero)
# ═══════════════════════════════════════════════════════════════
from models import DatabaseManager
from config import DB_PATH  # Importar DB_PATH
db = DatabaseManager(app)
print(f"🗄️  DatabaseManager inicializado: {DB_PATH}")''')

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ DB_PATH import añadido")

