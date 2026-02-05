#!/usr/bin/env python3
"""
Fix: Arreglar bloques try vacíos
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

nuevas_lineas = []
i = 0

while i < len(lineas):
    linea = lineas[i]
    
    # Detectar try: seguido de línea comentada y except
    if linea.strip().startswith('try:'):
        nuevas_lineas.append(linea)
        i += 1
        
        # Ver siguiente línea
        if i < len(lineas):
            siguiente = lineas[i]
            
            # Si la siguiente está comentada y luego viene except
            if siguiente.strip().startswith('# COMENTADO'):
                # Añadir pass antes del comentario
                espacios = len(siguiente) - len(siguiente.lstrip())
                nuevas_lineas.append(' ' * (espacios + 4) + 'pass  # Bloque vacío\n')
                nuevas_lineas.append(siguiente)
                i += 1
            else:
                nuevas_lineas.append(siguiente)
                i += 1
    else:
        nuevas_lineas.append(linea)
        i += 1

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.writelines(nuevas_lineas)

print("✅ Bloques try arreglados")

