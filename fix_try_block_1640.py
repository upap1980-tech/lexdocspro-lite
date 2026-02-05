#!/usr/bin/env python3
"""
Corregir bloque try incompleto en línea 1640
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Ver contexto de línea 1640
print("📝 Contexto líneas 1638-1655:")
for i in range(1637, min(1655, len(lineas))):
    print(f"{i+1:4d}: {lineas[i]}", end='')

# Buscar el try en línea 1640
if len(lineas) > 1639:
    # Opción 1: Añadir except después de result = autoprocessor.start()
    # Buscar donde termina ese bloque try
    
    # Insertar except en línea 1643 (índice 1642)
    indent = '    '  # Nivel de indentación del try
    
    except_block = f'''{indent}except Exception as e:
{indent}    print(f"⚠️  Error iniciando AutoProcessor: {{e}}")
{indent}    pass

'''
    
    # Insertar después de la línea 1642 (antes del comentario IA Cascade)
    lineas.insert(1642, except_block)
    
    # Guardar
    with open('run.py', 'w', encoding='utf-8') as f:
        f.writelines(lineas)
    
    print("\n✅ Bloque except añadido")
    print(f"   Insertado después de línea 1642")

