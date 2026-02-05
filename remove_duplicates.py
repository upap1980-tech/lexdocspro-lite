#!/usr/bin/env python3
"""
Eliminar todas las funciones autoprocessor duplicadas excepto la primera
"""

with open('run.py', 'r', encoding='utf-8') as f:
    lineas = f.readlines()

# Buscar todas las definiciones de endpoints autoprocessor
endpoints_encontrados = {}
lineas_a_eliminar = set()

for i, linea in enumerate(lineas):
    # Detectar @app.route de autoprocessor
    if '@app.route' in linea and '/api/autoprocessor/' in linea:
        # Extraer endpoint
        endpoint = linea.split('/api/autoprocessor/')[1].split("'")[0]
        
        if endpoint in endpoints_encontrados:
            # DUPLICADO - marcar para eliminar
            print(f"⚠️  DUPLICADO encontrado: {endpoint} en línea {i+1} (primera en {endpoints_encontrados[endpoint]+1})")
            
            # Marcar desde @app.route hasta el siguiente @app.route o final
            start = i
            end = i + 1
            
            # Buscar hasta dónde llega esta función
            indent_base = len(lineas[i]) - len(lineas[i].lstrip())
            
            for j in range(i+1, len(lineas)):
                # Si encontramos otro @app.route, terminamos
                if lineas[j].strip().startswith('@app.route'):
                    end = j
                    break
                
                # Si encontramos código al mismo nivel de indentación, terminamos
                if lineas[j].strip() and not lineas[j].strip().startswith('#'):
                    current_indent = len(lineas[j]) - len(lineas[j].lstrip())
                    if current_indent <= indent_base:
                        end = j
                        break
            
            # Marcar líneas para eliminar
            for k in range(start, end):
                lineas_a_eliminar.add(k)
            
            print(f"   Marcadas líneas {start+1} a {end}")
        else:
            # Primera vez que vemos este endpoint
            endpoints_encontrados[endpoint] = i
            print(f"✅ Endpoint {endpoint} en línea {i+1}")

# Crear archivo sin las líneas duplicadas
if lineas_a_eliminar:
    print(f"\n🗑️  Eliminando {len(lineas_a_eliminar)} líneas duplicadas...")
    
    nuevas_lineas = [linea for i, linea in enumerate(lineas) if i not in lineas_a_eliminar]
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.writelines(nuevas_lineas)
    
    print(f"✅ Duplicados eliminados")
    print(f"   Líneas antes: {len(lineas)}")
    print(f"   Líneas después: {len(nuevas_lineas)}")
else:
    print("\n✅ No hay duplicados")

