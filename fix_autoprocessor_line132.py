#!/usr/bin/env python3
"""
Corregir línea 132 de run.py
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Corregir línea 132 (índice 131)
if len(lineas) > 131:
    linea_actual = lineas[131]
    
    if 'autoprocessor = AutoProcessorService(ocr_service, ai_service)' in linea_actual:
        # Reemplazar con inicialización correcta
        lineas[131] = '''import os
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

'''
        
        # Guardar
        with open('run.py', 'w', encoding='utf-8') as f:
            f.writelines(lineas)
        
        print("✅ Línea 132 corregida")
        print("   - Añadido watch_dir")
        print("   - Añadida creación de carpeta")
        print("   - Añadido inicio automático")
    else:
        print("⚠️  Línea 132 no coincide con el patrón esperado")
        print(f"   Contenido actual: {linea_actual.strip()}")
else:
    print("❌ run.py tiene menos de 132 líneas")

