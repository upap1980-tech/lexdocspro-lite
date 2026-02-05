#!/usr/bin/env python3
"""
Añadir método get_processing_log al servicio
"""

with open('services/autoprocessor_service.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

if 'def get_processing_log' not in contenido:
    print("⚠️  Método get_processing_log NO existe, añadiendo...")
    
    # Método a añadir
    metodo = '''
    def get_processing_log(self, limit=50):
        """Obtener últimos registros del log de trazabilidad"""
        try:
            import sqlite3
            
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, status, error_message, ocr_chars, 
                       ai_analysis, processing_time, completed_at,
                       backup_path, final_path
                FROM processing_log
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'filename': row[0],
                    'status': row[1],
                    'error': row[2],
                    'ocr_chars': row[3],
                    'ai_analysis': row[4],
                    'processing_time': row[5],
                    'completed_at': row[6],
                    'backup_path': row[7],
                    'final_path': row[8]
                }
                for row in rows
            ]
            
        except Exception as e:
            print(f"❌ Error leyendo log: {e}")
            import traceback
            traceback.print_exc()
            return []
'''
    
    # Añadir antes del final de la clase
    # Buscar "def scan_existing_files" y añadir después
    if 'def scan_existing_files' in contenido:
        import re
        
        # Buscar el final del método scan_existing_files
        patron = r'(def scan_existing_files\(self\):.*?return files)'
        
        match = re.search(patron, contenido, re.DOTALL)
        if match:
            # Insertar después
            pos = match.end()
            contenido = contenido[:pos] + '\n' + metodo + contenido[pos:]
            
            with open('services/autoprocessor_service.py', 'w', encoding='utf-8') as f:
                f.write(contenido)
            
            print("✅ Método get_processing_log añadido")
        else:
            print("❌ No se encontró scan_existing_files")
    else:
        print("❌ No se encontró scan_existing_files")
else:
    print("✅ Método get_processing_log ya existe")

