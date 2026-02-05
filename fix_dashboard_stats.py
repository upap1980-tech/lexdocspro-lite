#!/usr/bin/env python3
"""
Fix: Crear endpoint funcional /api/dashboard/stats
"""

with open('run.py', 'r', encoding='utf-8') as f:
    contenido = f.read()

# Buscar si ya existe un endpoint de dashboard
if '@app.route(\'/api/dashboard/stats' not in contenido and '@app.route("/api/dashboard/stats' not in contenido:
    # Añadir endpoint ANTES del if __name__
    endpoint_dashboard = '''
# ═══════════════════════════════════════════════════════════════
# DASHBOARD STATS ENDPOINT
# ═══════════════════════════════════════════════════════════════

@app.route('/api/dashboard/stats', methods=['GET'])
@jwt_required()
def dashboard_stats():
    """
    Estadísticas del dashboard en tiempo real
    """
    try:
        from datetime import date
        conn = db.get_connection()
        cursor = conn.cursor()
        
        # Documentos procesados hoy
        today = date.today()
        cursor.execute("""
            SELECT COUNT(*) 
            FROM saved_documents 
            WHERE DATE(created_at) = ?
        """, (today,))
        docs_hoy = cursor.fetchone()[0]
        
        # Documentos en revisión
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'pending'
        """)
        en_revision = cursor.fetchone()[0]
        
        # Errores (documentos rechazados hoy)
        cursor.execute("""
            SELECT COUNT(*) 
            FROM pending_documents 
            WHERE status = 'rejected' 
            AND DATE(created_at) = ?
        """, (today,))
        errores = cursor.fetchone()[0]
        
        # Alertas LexNET urgentes
        cursor.execute("""
            SELECT COUNT(*) 
            FROM notifications 
            WHERE urgency IN ('CRITICAL', 'URGENT') 
            AND read = 0
        """)
        alertas = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'procesos_hoy': docs_hoy,
            'en_revision': en_revision,
            'errores': errores,
            'alertas': alertas
        }), 200
        
    except Exception as e:
        print(f"❌ Error en dashboard stats: {e}")
        return jsonify({
            'success': False,
            'procesos_hoy': 0,
            'en_revision': 0,
            'errores': 0,
            'alertas': 0
        }), 200  # Devolver 200 con valores 0

'''
    
    # Insertar antes del if __name__
    if "if __name__ == '__main__':" in contenido:
        partes = contenido.rsplit("if __name__ == '__main__':", 1)
        contenido = partes[0] + endpoint_dashboard + "\nif __name__ == '__main__':" + partes[1]
    else:
        contenido += endpoint_dashboard
    
    # Guardar
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(contenido)
    
    print("✅ Endpoint /api/dashboard/stats creado")
else:
    print("⚠️  Endpoint ya existe, verificando estructura...")
    
    # Verificar que devuelve los campos correctos
    if "'procesos_hoy'" not in contenido or '"procesos_hoy"' not in contenido:
        print("❌ El endpoint existe pero no devuelve los campos correctos")
        print("   Edita manualmente el endpoint para que devuelva:")
        print("   - procesos_hoy")
        print("   - en_revision")
        print("   - errores")
        print("   - alertas")
    else:
        print("✅ Endpoint parece correcto")

