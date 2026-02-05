#!/usr/bin/env python3
"""
Eliminar TODAS las apariciones duplicadas de autoprocessor
"""

import shutil
from datetime import datetime

def fix_all_duplicates():
    run_py_path = 'run.py'
    
    # Backup
    backup_path = f'run.py.backup_final_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
    shutil.copy(run_py_path, backup_path)
    print(f"✅ Backup creado: {backup_path}")
    
    # Leer archivo
    with open(run_py_path, 'r') as f:
        lines = f.readlines()
    
    print(f"📊 Total líneas: {len(lines)}")
    
    # Buscar TODAS las apariciones de autoprocessor_log
    log_appearances = []
    for i, line in enumerate(lines):
        if 'def autoprocessor_log(' in line:
            log_appearances.append(i)
            print(f"🔍 autoprocessor_log encontrado en línea {i+1}")
    
    if len(log_appearances) <= 1:
        print("✅ No hay duplicados de autoprocessor_log")
        return
    
    print(f"\n⚠️  {len(log_appearances)} apariciones de autoprocessor_log")
    print("📍 Mantendremos la PRIMERA, eliminaremos el resto")
    
    # Mantener la primera aparición
    keep_line = log_appearances[0]
    print(f"✅ MANTENER: línea {keep_line+1}")
    
    # Eliminar las demás
    delete_ranges = []
    for dup_line in log_appearances[1:]:
        print(f"🗑️  ELIMINAR: línea {dup_line+1}")
        
        # Encontrar el rango completo de la función
        # Buscar decorador anterior
        decorator_line = dup_line - 1
        while decorator_line >= 0 and lines[decorator_line].strip().startswith('@'):
            decorator_line -= 1
        decorator_line += 1
        
        # Buscar final de función (siguiente def/@ o fin de archivo)
        end_line = dup_line + 1
        indent = len(lines[dup_line]) - len(lines[dup_line].lstrip())
        
        while end_line < len(lines):
            line = lines[end_line]
            if line.strip() == '':
                end_line += 1
                continue
            
            curr_indent = len(line) - len(line.lstrip())
            if (line.strip().startswith(('def ', '@app.route', '# ═')) and curr_indent <= indent):
                break
            
            end_line += 1
        
        delete_ranges.append((decorator_line, end_line))
        print(f"   Rango: líneas {decorator_line+1} a {end_line}")
    
    # Eliminar rangos en orden inverso (para no afectar índices)
    lines_to_delete = set()
    for start, end in delete_ranges:
        for i in range(start, end):
            lines_to_delete.add(i)
    
    # Crear nuevo contenido
    new_lines = [line for i, line in enumerate(lines) if i not in lines_to_delete]
    
    # Guardar
    with open(run_py_path, 'w') as f:
        f.writelines(new_lines)
    
    print(f"\n✅ Archivo limpiado")
    print(f"📊 Líneas eliminadas: {len(lines_to_delete)}")
    print(f"📊 Total antes: {len(lines)}")
    print(f"📊 Total después: {len(new_lines)}")
    
    # Verificar
    print(f"\n🔍 Verificando...")
    import subprocess
    result = subprocess.run(['python', '-m', 'py_compile', run_py_path],
                          capture_output=True, text=True)
    
    if result.returncode == 0:
        print("✅ SINTAXIS CORRECTA")
    else:
        print("❌ ERROR DE SINTAXIS:")
        print(result.stderr)

if __name__ == '__main__':
    fix_all_duplicates()

