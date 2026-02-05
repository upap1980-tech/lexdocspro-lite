#!/usr/bin/env python3
"""
Script para eliminar duplicados específicos en run.py
"""

import shutil
from datetime import datetime

def fix_duplicates():
    run_py_path = 'run.py'
    
    # Backup
    backup_path = f'run.py.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy(run_py_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Leer archivo
    with open(run_py_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    print(f"📊 Total de líneas: {len(lines)}")
    
    # Estrategia: Eliminar líneas 1950-1989 (índices 1949-1988 en Python, base 0)
    # Ajustar según el número exacto de líneas del bloque duplicado
    
    start_delete = 1950  # Línea 1951 en editor (base 1)
    end_delete = 1990    # Línea 1990 en editor (base 1)
    
    # Convertir a índices Python (base 0)
    start_idx = start_delete - 1
    end_idx = end_delete
    
    print(f"\n🗑️  Eliminando líneas {start_delete} a {end_delete}...")
    print(f"   (Índices Python: {start_idx} a {end_idx})")
    
    # Mostrar preview de lo que se eliminará
    print(f"\n📄 PREVIEW DE LÍNEAS A ELIMINAR:")
    print("─" * 70)
    for i in range(start_idx, min(start_idx + 10, end_idx)):
        if i < len(lines):
            print(f"{i+1:4d}: {lines[i]}", end='')
    print("   ...")
    for i in range(max(start_idx + 10, end_idx - 5), end_idx):
        if i < len(lines):
            print(f"{i+1:4d}: {lines[i]}", end='')
    print("─" * 70)
    
    # Confirmar
    confirm = input("\n¿Continuar con la eliminación? (s/n): ")
    if confirm.lower() != 's':
        print("❌ Operación cancelada")
        return
    
    # Crear nuevo contenido eliminando el bloque
    new_lines = lines[:start_idx] + lines[end_idx:]
    
    # Guardar
    with open(run_py_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ Archivo limpiado")
    print(f"📊 Líneas eliminadas: {end_idx - start_idx}")
    print(f"📊 Líneas totales antes: {len(lines)}")
    print(f"📊 Líneas totales después: {len(new_lines)}")
    
    # Verificar que ya no hay duplicados
    print("\n🔍 Verificando duplicados restantes...")
    
    with open(run_py_path, 'r') as f:
        content = f.read()
    
    import re
    reset_count = len(re.findall(r'def autoprocessor_reset\(', content))
    scan_count = len(re.findall(r'def autoprocessor_scan\(', content))
    
    print(f"   autoprocessor_reset: {reset_count} apariciones")
    print(f"   autoprocessor_scan: {scan_count} apariciones")
    
    if reset_count == 1 and scan_count == 1:
        print("\n✅ TODOS LOS DUPLICADOS ELIMINADOS")
    else:
        print("\n⚠️  AÚN HAY DUPLICADOS. Revisar manualmente.")

if __name__ == '__main__':
    fix_duplicates()

