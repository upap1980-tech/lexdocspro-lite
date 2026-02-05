#!/usr/bin/env python3
"""
Fix: Conectar dashboard frontend con backend
"""
import os
import glob

# Buscar archivos JS
js_files = glob.glob('static/js/*.js')

for js_file in js_files:
    with open(js_file, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    # Verificar si tiene código de dashboard
    if 'dashboard' in contenido.lower() or 'procesos' in contenido.lower():
        print(f"\n📄 Encontrado dashboard code en: {js_file}")
        
        # Verificar si hace fetch al endpoint correcto
        if '/api/dashboard/stats' not in contenido:
            print(f"⚠️  No encontrado fetch a /api/dashboard/stats")
            print(f"   Archivo: {js_file}")
            
            # Mostrar líneas relevantes
            lineas = contenido.split('\n')
            for i, linea in enumerate(lineas, 1):
                if 'fetch' in linea.lower() and ('dashboard' in linea.lower() or 'stats' in linea.lower()):
                    print(f"   Línea {i}: {linea.strip()}")

# Buscar en HTML templates
html_files = glob.glob('templates/*.html')

for html_file in html_files:
    with open(html_file, 'r', encoding='utf-8') as f:
        contenido = f.read()
    
    if 'procesos_hoy' in contenido or 'en_revision' in contenido:
        print(f"\n📄 Dashboard HTML encontrado en: {html_file}")
        
        # Ver IDs de elementos
        import re
        ids = re.findall(r'id=["\']([^"\']*(?:hoy|rev|err|ale)[^"\']*)["\']', contenido)
        if ids:
            print(f"   IDs encontrados: {ids}")

print("\n✅ Análisis completado")

