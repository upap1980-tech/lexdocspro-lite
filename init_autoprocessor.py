#!/usr/bin/env python3
"""
Inicializar AutoProcessor en run.py
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar la sección de servicios
if 'from services.auto_processor_service import AutoProcessorService' not in contenido:
    
    # Añadir import
    import_line = "from services.auto_processor_service import AutoProcessorService\n"
    
    # Buscar donde están los otros imports de servicios
    if 'from services.ocr_service import OCRService' in contenido:
        contenido = contenido.replace(
            'from services.ocr_service import OCRService',
            'from services.ocr_service import OCRService\n' + import_line
        )
    else:
        # Añadir al inicio después de imports de Flask
        contenido = contenido.replace(
            'from flask import',
            import_line + 'from flask import'
        )
    
    print("✅ Import de AutoProcessorService añadido")

# Inicializar el servicio
if 'autoprocessor = AutoProcessorService' not in contenido:
    
    # Buscar donde se inicializan otros servicios
    init_code = '''
# Inicializar Auto-Processor
PENDIENTES_DIR = os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS")
autoprocessor = AutoProcessorService(
    watch_dir=PENDIENTES_DIR,
    ocr_service=ocr_service if 'ocr_service' in locals() else None,
    ai_service=ai_service if 'ai_service' in locals() else None
)
# Iniciar automáticamente
autoprocessor.start()
'''
    
    # Insertar después de otros servicios
    if 'ocr_service = OCRService()' in contenido:
        contenido = contenido.replace(
            'ocr_service = OCRService()',
            'ocr_service = OCRService()\n' + init_code
        )
    else:
        # Insertar antes de crear la app
        contenido = contenido.replace(
            'app = Flask(__name__)',
            init_code + '\napp = Flask(__name__)'
        )
    
    print("✅ Inicialización de AutoProcessor añadida")

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ run.py actualizado con AutoProcessor")

