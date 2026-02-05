#!/bin/bash

echo "🔧 Arreglando archivos de AutoProcessor..."

# 1. Respaldar viejo
mv services/autoprocessor_service.py services/autoprocessor_service.py.OLD 2>/dev/null

# 2. Copiar nuevo
cp services/auto_processor_service.py services/autoprocessor_service.py

# 3. Verificar línea 132 de run.py
echo ""
echo "📝 Verificando run.py línea 132..."
sed -n '131,135p' run.py

# 4. Corregir si es necesario
python3 <<'EOFPYTHON'
with open('run.py', 'r') as f:
    lineas = f.readlines()

if len(lineas) > 131:
    linea = lineas[131]
    
    if 'autoprocessor = AutoProcessorService(ocr_service, ai_service)' in linea:
        print("❌ Línea 132 incorrecta, corrigiendo...")
        
        # Reemplazar líneas 131-132
        lineas[131] = '''import os
PENDIENTES_DIR = os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS")
os.makedirs(PENDIENTES_DIR, exist_ok=True)
autoprocessor = AutoProcessorService(
    watch_dir=PENDIENTES_DIR,
    ocr_service=ocr_service if 'ocr_service' in locals() else None,
    ai_service=ai_service if 'ai_service' in locals() else None
)
# Iniciar automáticamente
if autoprocessor.start():
    print(f"✅ AutoProcessor iniciado: {PENDIENTES_DIR}")

'''
        
        with open('run.py', 'w') as f:
            f.writelines(lineas)
        
        print("✅ run.py corregido")
    else:
        print("✅ Línea 132 ya está correcta")

EOFPYTHON

echo ""
echo "✅ Fix completado"
echo ""
echo "🔄 Ahora ejecuta:"
echo "   pkill -f 'python run.py'"
echo "   python run.py"

