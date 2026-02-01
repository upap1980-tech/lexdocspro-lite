#!/usr/bin/env python3
"""
Auto-procesador de documentos legales
Monitorea carpeta PENDIENTES y procesa documentos automáticamente
"""

import os
import time
import requests
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

PENDIENTES_DIR = os.path.expanduser('/Users/victormfrancisco/Desktop/PENDIENTES_LEXDOCS')
API_URL = 'http://localhost:5001'

class DocumentHandler(FileSystemEventHandler):
    def on_created(self, event):
        if event.is_directory:
            return
        
        filepath = event.src_path
        filename = os.path.basename(filepath)
        
        # Ignorar archivos temporales
        if filename.startswith('.'):
            return
        
        print(f"\n📄 Nuevo documento detectado: {filename}")
        time.sleep(2)  # Esperar a que termine de copiarse
        
        # Analizar documento
        try:
            with open(filepath, 'rb') as f:
                files = {'file': f}
                print("🔍 Analizando con IA...")
                response = requests.post(
                    f'{API_URL}/api/document/smart-analyze',
                    files=files,
                    timeout=60
                )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('success'):
                    cliente = data['cliente_propuesto']
                    metadata = data['metadata']
                    
                    print(f"\n📊 ANÁLISIS:")
                    print(f"   Cliente: {cliente['carpeta']}")
                    print(f"   Tipo: {metadata['tipo_documento']}")
                    print(f"   Archivo sugerido: {data['nombre_archivo_sugerido']}")
                    print(f"   Ruta: {data['ruta_relativa']}")
                    
                    # Mostrar notificación macOS
                    os.system(f'''
                        osascript -e 'display notification "Cliente: {cliente['carpeta']}" with title "📄 Documento detectado" sound name "default"'
                    ''')
                    
                    # Pedir confirmación
                    print("\n¿Guardar documento? (s/n): ", end='')
                    respuesta = input().lower()
                    
                    if respuesta == 's':
                        # Guardar documento
                        save_response = requests.post(
                            f'{API_URL}/api/document/save-organized',
                            json={
                                'temp_file_path': data['temp_file_path'],
                                'dest_path': data['ruta_completa']
                            }
                        )
                        
                        if save_response.status_code == 200:
                            print("✅ Documento guardado correctamente")
                            
                            # Eliminar de PENDIENTES
                            try:
                                os.remove(filepath)
                                print(f"🗑️  Eliminado de PENDIENTES")
                            except:
                                pass
                            
                            # Notificación de éxito
                            os.system(f'''
                                osascript -e 'display notification "Guardado en {data['ruta_relativa']}" with title "✅ Documento guardado" sound name "Glass"'
                            ''')
                        else:
                            print(f"❌ Error al guardar: {save_response.text}")
                    else:
                        print("❌ Cancelado")
                else:
                    print(f"❌ Error en análisis: {data.get('error')}")
            else:
                print(f"❌ Error HTTP: {response.status_code}")
                
        except Exception as e:
            print(f"❌ Error: {str(e)}")

def main():
    print("🚀 Iniciando monitor de documentos...")
    print(f"📁 Monitoreando: {PENDIENTES_DIR}")
    print("⏸️  Presiona Ctrl+C para detener\n")
    
    # Crear carpeta si no existe
    os.makedirs(PENDIENTES_DIR, exist_ok=True)
    
    event_handler = DocumentHandler()
    observer = Observer()
    observer.schedule(event_handler, PENDIENTES_DIR, recursive=False)
    observer.start()
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
        print("\n\n👋 Monitor detenido")
    
    observer.join()

if __name__ == '__main__':
    main()

