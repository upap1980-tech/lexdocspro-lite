#!/usr/bin/env python3
"""
Fix: Reemplazar métodos inexistentes por SQL directo
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar la función dashboard_stats y reemplazarla completamente
import re

# Patrón para encontrar toda la función
patron = r'@app\.route\(\'/api/dashboard/stats\'[^\n]*\n@jwt_required\(\)\ndef dashboard_stats\(\):.*?(?=\n@app\.route|\nif __name__|$)'

nueva_funcion = '''@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """Obtener estadísticas del dashboard en tiempo real (versión SQL directa)"""
    try:
        from datetime import date
        import sqlite3
        
        # Obtener conexión a la base de datos
        conn = sqlite3.connect(db.db_path if hasattr(db, 'db_path') else 'lexdocs.db')
        cursor = conn.cursor()
        
        # Documentos procesados hoy
        today = date.today().isoformat()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM saved_documents 
            WHERE DATE(created_at) = ?
        """, (today,))
        docs_today = cursor.fetchone()[0] or 0
        
        # Documentos pendientes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'pending'
        """)
        pending = cursor.fetchone()[0] or 0
        
        # Errores (documentos rechazados hoy)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'rejected' 
            AND DATE(created_at) = ?
        """, (today,))
        errores = cursor.fetchone()[0] or 0
        
        # Alertas LexNET urgentes (si existe la tabla)
        try:
            cursor.execute("""
                SELECT COUNT(*) 
                FROM notifications 
                WHERE urgency IN ('CRITICAL', 'URGENT') 
                AND read = 0
            """)
            alertas = cursor.fetchone()[0] or 0
        except:
            alertas = 0
        
        conn.close()
        
        return jsonify({
            'success': True,
            'procesos_hoy': docs_today,
            'en_revision': pending,
            'errores': errores,
            'alertas': alertas
        }), 200
    
    except Exception as e:
        print(f"❌ Error obteniendo stats: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # Devolver valores por defecto
        return jsonify({
            'success': False,
            'procesos_hoy': 0,
            'en_revision': 0,
            'errores': 0,
            'alertas': 0,
            'error': str(e)
        }), 200  # 200 para que el frontend no falle

'''

# Reemplazar
contenido = re.sub(patron, nueva_funcion, contenido, flags=re.DOTALL)

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido)

print("✅ Función dashboard_stats reemplazada con SQL directo")
print("🔄 Reinicia el servidor")

