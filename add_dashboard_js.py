with open('templates/index.html', 'r') as f:
    contenido = f.read()

if 'dashboard.js' not in contenido:
    # Buscar el </body> y añadir antes
    if '</body>' in contenido:
        contenido = contenido.replace(
            '</body>',
            '    <script src="{{ url_for(\'static\', filename=\'js/dashboard.js\') }}"></script>\n</body>'
        )
        
        with open('templates/index.html', 'w') as f:
            f.write(contenido)
        
        print("✅ dashboard.js añadido al HTML")
    else:
        print("⚠️  No se encontró </body> en index.html")
else:
    print("✅ dashboard.js ya está incluido")

