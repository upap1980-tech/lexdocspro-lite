#!/usr/bin/env bash
# add_autoprocesador_api.sh - Añadir rutas API al backend

echo "🔧 Añadiendo APIs del Auto-Procesador a run.py..."

# Backup
cp run.py run.py.backup_api_$(date +%Y%m%d_%H%M%S)

# Crear el código de las APIs
cat > _autoprocesador_api.py <<'APIEOF'

# ============================================
# AUTO-PROCESADOR API ENDPOINTS
# ============================================

@app.route('/api/autoprocesador/stats', methods=['GET'])
def autoprocesador_stats():
    """Obtener estadísticas del auto-procesador"""
    try:
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        cur = conn.cursor()
        
        # Obtener fecha de hoy
        hoy = datetime.now().strftime('%Y%m%d')
        
        # Total documentos hoy
        cur.execute("SELECT COUNT(*) FROM documentos WHERE fecha_procesamiento = ?", (hoy,))
        total_hoy = cur.fetchone()[0]
        
        # Automáticos
        cur.execute("SELECT COUNT(*) FROM documentos WHERE fecha_procesamiento = ? AND estado = 'auto'", (hoy,))
        automaticos = cur.fetchone()[0]
        
        # En revisión
        cur.execute("SELECT COUNT(*) FROM documentos WHERE fecha_procesamiento = ? AND estado = 'revision'", (hoy,))
        en_revision = cur.fetchone()[0]
        
        # Errores
        cur.execute("SELECT COUNT(*) FROM documentos WHERE fecha_procesamiento = ? AND estado = 'error'", (hoy,))
        errores = cur.fetchone()[0]
        
        conn.close()
        
        # Calcular porcentajes
        porcentaje_auto = round((automaticos / total_hoy * 100) if total_hoy > 0 else 0, 1)
        porcentaje_revision = round((en_revision / total_hoy * 100) if total_hoy > 0 else 0, 1)
        porcentaje_errores = round((errores / total_hoy * 100) if total_hoy > 0 else 0, 1)
        
        return jsonify({
            'success': True,
            'stats': {
                'total_hoy': total_hoy,
                'automaticos': automaticos,
                'en_revision': en_revision,
                'errores': errores,
                'porcentaje_auto': porcentaje_auto,
                'porcentaje_revision': porcentaje_revision,
                'porcentaje_errores': porcentaje_errores
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocesador/cola-revision', methods=['GET'])
def autoprocesador_cola_revision():
    """Obtener documentos en cola de revisión"""
    try:
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("""
            SELECT * FROM documentos 
            WHERE estado = 'revision'
            ORDER BY fecha_procesamiento DESC, id DESC
        """)
        
        rows = cur.fetchall()
        documentos = [dict(row) for row in rows]
        conn.close()
        
        return jsonify({
            'success': True,
            'documentos': documentos,
            'total': len(documentos)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocesador/clientes', methods=['GET'])
def autoprocesador_clientes():
    """Obtener lista de clientes"""
    try:
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT codigo, nombre FROM clientes ORDER BY nombre")
        rows = cur.fetchall()
        clientes = [dict(row) for row in rows]
        conn.close()
        
        return jsonify({
            'success': True,
            'clientes': clientes
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocesador/documento/<int:doc_id>', methods=['GET'])
def autoprocesador_documento(doc_id):
    """Obtener detalles de un documento"""
    try:
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        cur.execute("SELECT * FROM documentos WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        documento = dict(row)
        return jsonify({
            'success': True,
            'documento': documento
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocesador/pdf/<int:doc_id>', methods=['GET'])
def autoprocesador_pdf(doc_id):
    """Servir PDF de un documento"""
    try:
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        cur = conn.cursor()
        
        cur.execute("SELECT ruta_temporal FROM documentos WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        
        if not row:
            return "Documento no encontrado", 404
        
        ruta_pdf = row[0]
        
        if not os.path.exists(ruta_pdf):
            return f"Archivo no encontrado: {ruta_pdf}", 404
        
        return send_file(ruta_pdf, mimetype='application/pdf')
    except Exception as e:
        return f"Error: {str(e)}", 500

@app.route('/api/autoprocesador/aprobar/<int:doc_id>', methods=['POST'])
def autoprocesador_aprobar(doc_id):
    """Aprobar un documento y moverlo a su ubicación definitiva"""
    try:
        data = request.get_json()
        usuario_modifico = data.get('usuario_modifico', False)
        cliente_codigo = data.get('cliente_codigo')
        tipo_documento = data.get('tipo_documento')
        
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        cur = conn.cursor()
        
        # Obtener documento
        cur.execute("SELECT * FROM documentos WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            conn.close()
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Construir ruta definitiva
        if cliente_codigo and tipo_documento:
            año = datetime.now().year
            carpeta_base = f"EXPEDIENTES/{año}/{cliente_codigo}"
            
            # Crear subcarpeta según tipo
            subcarpetas = {
                'Contrato': 'Contratos',
                'Factura': 'Facturas',
                'Escritura': 'Escrituras',
                'Sentencia': 'Sentencias',
                'Demanda': 'Demandas'
            }
            subcarpeta = subcarpetas.get(tipo_documento, 'Otros')
            
            ruta_definitiva = f"{carpeta_base}/{subcarpeta}"
            
            # Crear directorio si no existe
            os.makedirs(ruta_definitiva, exist_ok=True)
            
            # Mover archivo
            nombre_archivo = doc[1]  # archivo_original
            ruta_destino = os.path.join(ruta_definitiva, nombre_archivo)
            
            # Si el archivo existe en temporal, moverlo
            if os.path.exists(doc[2]):  # ruta_temporal
                shutil.move(doc[2], ruta_destino)
            
            # Actualizar BD
            cur.execute("""
                UPDATE documentos 
                SET estado = 'aprobado', 
                    usuario_modifico = ?,
                    cliente_codigo = ?,
                    tipo_documento = ?,
                    ruta_definitiva = ?
                WHERE id = ?
            """, (1 if usuario_modifico else 0, cliente_codigo, tipo_documento, ruta_destino, doc_id))
            
            conn.commit()
            conn.close()
            
            return jsonify({
                'success': True,
                'ruta_destino': ruta_destino,
                'message': 'Documento aprobado y guardado'
            })
        else:
            conn.close()
            return jsonify({'success': False, 'error': 'Faltan cliente_codigo o tipo_documento'}), 400
            
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocesador/rechazar/<int:doc_id>', methods=['POST'])
def autoprocesador_rechazar(doc_id):
    """Rechazar un documento y moverlo a revisión manual"""
    try:
        data = request.get_json()
        motivo = data.get('motivo', 'Sin motivo especificado')
        
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        cur = conn.cursor()
        
        # Obtener documento
        cur.execute("SELECT * FROM documentos WHERE id = ?", (doc_id,))
        doc = cur.fetchone()
        
        if not doc:
            conn.close()
            return jsonify({'success': False, 'error': 'Documento no encontrado'}), 404
        
        # Crear carpeta de revisión manual
        carpeta_revision = "REVISAR_MANUAL"
        os.makedirs(carpeta_revision, exist_ok=True)
        
        # Mover archivo
        nombre_archivo = doc[1]  # archivo_original
        ruta_destino = os.path.join(carpeta_revision, nombre_archivo)
        
        if os.path.exists(doc[2]):  # ruta_temporal
            shutil.move(doc[2], ruta_destino)
        
        # Actualizar BD
        cur.execute("""
            UPDATE documentos 
            SET estado = 'rechazado',
                ruta_definitiva = ?
            WHERE id = ?
        """, (ruta_destino, doc_id))
        
        conn.commit()
        conn.close()
        
        return jsonify({
            'success': True,
            'message': f'Documento rechazado: {motivo}',
            'ruta_destino': ruta_destino
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/autoprocesador/procesados-hoy', methods=['GET'])
def autoprocesador_procesados_hoy():
    """Obtener todos los documentos procesados hoy"""
    try:
        conn = sqlite3.connect('lexdocs_autoprocesador.db')
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        
        hoy = datetime.now().strftime('%Y%m%d')
        
        cur.execute("""
            SELECT * FROM documentos 
            WHERE fecha_procesamiento = ?
            ORDER BY id DESC
        """, (hoy,))
        
        rows = cur.fetchall()
        documentos = [dict(row) for row in rows]
        conn.close()
        
        return jsonify({
            'success': True,
            'documentos': documentos,
            'total': len(documentos)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
APIEOF

# Insertar las APIs antes del if __name__ == '__main__' en run.py
python3 <<'PYEOF'
with open('run.py', 'r', encoding='utf-8') as f:
    content = f.read()

with open('_autoprocesador_api.py', 'r', encoding='utf-8') as f:
    api_code = f.read()

# Buscar la línea if __name__ == '__main__':
marker = "if __name__ == '__main__':"

if marker in content:
    parts = content.split(marker, 1)
    new_content = parts[0] + api_code + '\n\n' + marker + parts[1]
    
    with open('run.py', 'w', encoding='utf-8') as f:
        f.write(new_content)
    
    print("✓ APIs añadidas correctamente a run.py")
else:
    print("✗ No se encontró el marcador if __name__")
PYEOF

# Limpiar
rm _autoprocesador_api.py

echo ""
echo "✅ APIs del Auto-Procesador añadidas"
echo ""
echo "🔄 Reinicia Flask: python run.py"
echo "🔄 Recarga el navegador y prueba la pestaña Auto-Procesador"
