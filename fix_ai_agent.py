#!/usr/bin/env python3
"""
Fix: Eliminar referencias a ai_agent que no existe
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Reemplazar todas las referencias a ai_agent
contenido = contenido.replace(
    'doc_generator = DocumentGenerator(ai_service, ai_agent)',
    'doc_generator = DocumentGenerator(ai_service)'
)

contenido = contenido.replace(
    'lexnet_service = LexNetNotifications(db_manager=db, ai_agent=ai_agent)',
    'lexnet_service = LexNetNotifications(db_manager=db)'
)

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Referencias a ai_agent eliminadas")

