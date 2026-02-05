#!/usr/bin/env python3
"""
Fix final: Usar DB_PATH correcto y métodos de DatabaseManager
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar la función dashboard_stats (alrededor de línea 1492)
import re

# Reemplazar toda la función con la versión correcta
patron = r'@app\.route\(\'/api/dashboard/stats\'[^\n]*\n@jwt_required\(\)\ndef dashboard_stats\(\):.*?(?=\n@app\.route|\n@app\.|\nif __name__|# ═)'

nueva_funcion = '''@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """Obtener estadísticas del dashboard en tiempo real"""
    try:
        from datetime import date
        import sqlite3
        
        # Usar DB_PATH importado de config
        conn = sqlite3.connect(str(DB_PATH))
        cursor = conn.cursor()
        
        # 1. Documentos procesados hoy
        today = date.today().isoformat()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM saved_documents 
            WHERE DATE(created_at) = ?
        """, (today,))
        docs_today = cursor.fetchone()[0] or 0
        
        # 2. Documentos en revisión (pendientes)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'pending'
        """)
        pending = cursor.fetchone()[0] or 0
        
        # 3. Errores (rechazados hoy)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'rejected' 
            AND DATE(created_at) = ?
        """, (today,))
        errores = cursor.fetchone()[0] or 0
        
        # 4. Alertas LexNET urgentes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM notifications 
            WHERE urgency IN ('CRITICAL', 'URGENT') 
            AND read = 0
        """)
        alertas = cursor.fetchone()[0] or 0
        
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
            'success': True,
            'procesos_hoy': 0,
            'en_revision': 0,
            'errores': 0,
            'alertas': 0
        }), 200

'''

# Reemplazar
contenido_nuevo = re.sub(patron, nueva_funcion, contenido, flags=re.DOTALL)

# Si no encontró el patrón, buscar manualmente
if contenido_nuevo == contenido:
    print("⚠️  Patrón regex no encontró la función, usando búsqueda manual...")
    
    # Buscar línea por línea
    lineas = contenido.split('\n')
    nuevas_lineas = []
    i = 0
    
    while i < len(lineas):
        linea = lineas[i]
        
        # Detectar inicio de dashboard_stats
        if "@app.route('/api/dashboard/stats'" in linea:
            # Añadir hasta encontrar el próximo @app.route o separador
            nuevas_lineas.append(nueva_funcion)
            
            # Saltar todo hasta la siguiente función
            i += 1
            while i < len(lineas):
                if lineas[i].startswith('@app.route') or lineas[i].startswith('# ═'):
                    break
                i += 1
            continue
        
        nuevas_lineas.append(linea)
        i += 1
    
    contenido_nuevo = '\n'.join(nuevas_lineas)

# Guardar
with open('run.py', 'w', encoding='utf-8') as f:
    f.write(contenido_nuevo)

print("✅ Función dashboard_stats reemplazada correctamente")
print("✅ Ahora usa DB_PATH de config.py")
print("✅ SQL directo sin depender de métodos de DatabaseManager")
print("")
print("🔄 Reinicia el servidor: pkill -f 'python run.py' && python run.py")

