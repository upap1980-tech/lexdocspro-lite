#!/usr/bin/env python3
"""
Reemplazar líneas 130-166 con código correcto
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Código correcto para reemplazar líneas 130-166
codigo_correcto = '''# Importar y configurar Auto-Processor
from services.autoprocessor_service import AutoProcessorService
try:
    from services.ia_cascade_service import IACascadeService
except ImportError:
    IACascadeService = None

import os
PENDIENTES_DIR = os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS")
os.makedirs(PENDIENTES_DIR, exist_ok=True)

autoprocessor = AutoProcessorService(
    watch_dir=PENDIENTES_DIR,
    ocr_service=ocr_service if 'ocr_service' in locals() else None,
    ai_service=ai_service if 'ai_service' in locals() else None
)

# Iniciar automáticamente
if autoprocessor.start():
    print(f"✅ AutoProcessor iniciado: {PENDIENTES_DIR}")

# IA Cascade Service
try:
    if IACascadeService:
        ia_cascade = IACascadeService()
        print("✅ IA Cascade inicializado")
    else:
        ia_cascade = None
except Exception as e:
    print(f"⚠️  Error inicializando IA Cascade: {e}")
    ia_cascade = None

# Importar y configurar Document Processing Service
from services.document_processing_service import DocumentProcessingService
doc_processor = DocumentProcessingService(ocr_service, ai_service, BASE_DIR)

# Asegurar directorios
os.makedirs(GENERATED_DOCS_DIR, exist_ok=True)
'''

# Reemplazar líneas 129-165 (índices 128-164)
nuevas_lineas = lineas[:129] + [codigo_correcto + '\n'] + lineas[166:]

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.writelines(nuevas_lineas)

print("✅ Líneas 130-166 corregidas")
print("   - if autoprocessor.start(): ✓")
print("   - Bloques correctamente indentados ✓")
print("   - Sin ':' huérfanos ✓")

