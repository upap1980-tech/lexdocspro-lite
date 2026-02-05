#!/usr/bin/env python3
"""
Fix: Encontrar y eliminar TODAS las inicializaciones incorrectas de DatabaseManager
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Buscar todas las líneas con DatabaseManager() sin argumentos
lineas_problematicas = []
for i, linea in enumerate(lineas, 1):
    if 'db = DatabaseManager()' in linea:
        lineas_problematicas.append(i)
        print(f"⚠️  Línea {i}: {linea.strip()}")

if not lineas_problematicas:
    print("✅ No se encontraron más instancias problemáticas")
else:
    print(f"\n🔧 Encontradas {len(lineas_problematicas)} líneas a corregir")
    
    # Comentar todas las líneas problemáticas
    nuevas_lineas = []
    for i, linea in enumerate(lineas, 1):
        if 'db = DatabaseManager()' in linea:
            # Comentar la línea
            nuevas_lineas.append(f"# COMENTADO - {linea}")
        else:
            nuevas_lineas.append(linea)
    
    # Guardar
    with open('run.py', 'w', encoding='utf-8') as f:
        f.writelines(nuevas_lineas)
    
    print(f"✅ {len(lineas_problematicas)} líneas comentadas")

print("\n📋 Verificando que la inicialización correcta existe...")

# Verificar que existe la inicialización correcta con (app)
with open('run.py', 'r') as f:
    contenido = f.read()

if 'db = DatabaseManager(app)' in contenido:
    print("✅ Inicialización correcta encontrada: db = DatabaseManager(app)")
else:
    print("⚠️  No se encontró la inicialización correcta")
    print("   Buscando mejor lugar para añadirla...")

