#!/usr/bin/env python3
"""
Verificar todos los bloques try tienen except/finally
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

in_try = False
try_line = 0
indent_level = 0

print("🔍 Verificando bloques try/except...")

for i, linea in enumerate(lineas, 1):
    stripped = linea.strip()
    
    # Detectar try
    if stripped.startswith('try:'):
        in_try = True
        try_line = i
        indent_level = len(linea) - len(linea.lstrip())
        print(f"  📍 try: en línea {i}")
    
    # Detectar except/finally con mismo nivel de indentación
    elif in_try and (stripped.startswith('except') or stripped.startswith('finally')):
        current_indent = len(linea) - len(linea.lstrip())
        if current_indent == indent_level:
            print(f"     ✅ {stripped[:20]} en línea {i}")
            in_try = False
    
    # Detectar nuevo bloque al mismo nivel (significa que el try no tiene except)
    elif in_try:
        current_indent = len(linea) - len(linea.lstrip())
        if current_indent == indent_level and stripped and not stripped.startswith('#'):
            if stripped.startswith('def ') or stripped.startswith('class ') or \
               stripped.startswith('if ') or stripped.startswith('for ') or \
               stripped.startswith('while ') or stripped.startswith('try:'):
                print(f"     ❌ SIN except/finally (termina antes de línea {i})")
                in_try = False

print("\n✅ Verificación completada")

