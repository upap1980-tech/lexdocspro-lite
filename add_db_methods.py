#!/usr/bin/env python3
"""
Añadir métodos faltantes a DatabaseManager en models.py
"""

with open('models.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Verificar si ya existen los métodos
if 'def count_documents_today' not in contenido:
    # Buscar la clase DatabaseManager
    if 'class DatabaseManager' in contenido:
        # Añadir métodos al final de la clase
        nuevos_metodos = '''
    
    def count_documents_today(self):
        """Contar documentos guardados hoy"""
        from datetime import date
        with self.db.engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text(
                "SELECT COUNT(*) FROM saved_documents WHERE DATE(created_at) = :today"
            ), {"today": date.today().isoformat()})
            return result.scalar() or 0
    
    def count_pending_documents(self):
        """Contar documentos pendientes"""
        with self.db.engine.connect() as conn:
            from sqlalchemy import text
            result = conn.execute(text(
                "SELECT COUNT(*) FROM pending_documents WHERE status = 'pending'"
            ))
            return result.scalar() or 0
'''
        
        # Insertar antes del final de la clase (buscar siguiente clase o EOF)
        import re
        # Buscar el final de DatabaseManager (siguiente class o EOF)
        patron = r'(class DatabaseManager.*?)(\nclass |\Z)'
        
        def reemplazo(match):
            return match.group(1) + nuevos_metodos + match.group(2)
        
        contenido = re.sub(patron, reemplazo, contenido, flags=re.DOTALL)
        
        # Guardar
        with open('models.py', 'w', encoding='utf-8') as f:
            f.write(contenido)
        
        print("✅ Métodos añadidos a DatabaseManager")
        print("   - count_documents_today()")
        print("   - count_pending_documents()")
    else:
        print("❌ No se encontró class DatabaseManager en models.py")
else:
    print("✅ Los métodos ya existen")

