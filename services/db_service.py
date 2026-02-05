"""
Database Service - Wrapper sobre models.py
"""
from datetime import date
import sqlite3
from config import DB_PATH

class DatabaseService:
    def __init__(self):
        self.db_path = str(DB_PATH)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def obtener_estadisticas_hoy(self):
        """Stats del día"""
        conn = self._connect()
        cursor = conn.cursor()
        
        today = date.today()
        
        cursor.execute("SELECT COUNT(*) FROM saved_documents WHERE DATE(created_at) = ?", (today,))
        total_hoy = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM pending_documents WHERE status = 'pending'")
        en_revision = cursor.fetchone()[0]
        
        conn.close()
        
        return {
            'total_hoy': total_hoy,
            'automaticos': int(total_hoy * 0.7),  # Estimado
            'en_revision': en_revision,
            'errores': 0
        }
    
    def obtener_cola_revision(self):
        """Docs pendientes"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pending_documents WHERE status = 'pending' LIMIT 50")
        rows = cursor.fetchall()
        conn.close()
        
        return [
            {
                'id': r['id'],
                'archivo_original': (
                    r['archivo_original'] if 'archivo_original' in r.keys()
                    else r['original_filename'] if 'original_filename' in r.keys()
                    else r['filename'] if 'filename' in r.keys()
                    else ''
                ),
                'estado': r['status'],
                'cliente_detectado': r['cliente_detectado'] if 'cliente_detectado' in r.keys() else '',
                'tipo_documento': r['tipo_documento'] if 'tipo_documento' in r.keys() else '',
                'confianza': r['confianza'] if 'confianza' in r.keys() else 0,
            }
            for r in rows
        ]
    
    def obtener_procesados_hoy(self):
        """Docs procesados hoy"""
        today = date.today()
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM saved_documents WHERE DATE(created_at) = ? LIMIT 50", (today,))
        rows = cursor.fetchall()
        conn.close()
        
        return [{'id': r['id'], 'filename': r['filename']} for r in rows]
    
    def obtener_documento(self, doc_id):
        """Obtener doc por ID"""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM pending_documents WHERE id = ?", (doc_id,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'id': row['id'],
                'ruta_temporal': (
                    row['ruta_temporal'] if 'ruta_temporal' in row.keys()
                    else row['temp_file_path'] if 'temp_file_path' in row.keys()
                    else ''
                ),
                'temp_file_path': (
                    row['ruta_temporal'] if 'ruta_temporal' in row.keys()
                    else row['temp_file_path'] if 'temp_file_path' in row.keys()
                    else ''
                ),
                'original_filename': (
                    row['archivo_original'] if 'archivo_original' in row.keys()
                    else row['original_filename'] if 'original_filename' in row.keys()
                    else ''
                ),
                'archivo_original': (
                    row['archivo_original'] if 'archivo_original' in row.keys()
                    else row['original_filename'] if 'original_filename' in row.keys()
                    else ''
                ),
                'cliente_codigo': row['cliente_codigo'] if 'cliente_codigo' in row.keys() else '',
                'cliente_detectado': row['cliente_detectado'] if 'cliente_detectado' in row.keys() else '',
                'tipo_documento': row['tipo_documento'] if 'tipo_documento' in row.keys() else '',
                'fecha_documento': row['fecha_documento'] if 'fecha_documento' in row.keys() else '',
                'carpeta_sugerida': row['carpeta_sugerida'] if 'carpeta_sugerida' in row.keys() else '',
                'confianza': row['confianza'] if 'confianza' in row.keys() else 0
            }
        return None
    
    def actualizar_documento(self, doc_id, updates):
        """Update doc"""
        if not updates:
            return
        conn = self._connect()
        cursor = conn.cursor()
        keys = []
        values = []
        for k, v in updates.items():
            keys.append(f"{k} = ?")
            values.append(v)
        values.append(doc_id)
        cursor.execute(
            f"UPDATE pending_documents SET {', '.join(keys)} WHERE id = ?",
            values
        )
        conn.commit()
        conn.close()
    
    def aprobar_documento(self, doc_id, ruta_destino, usuario_modifico):
        """Aprobar"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE pending_documents
            SET status = 'approved', ruta_destino = ?, usuario_modifico = ?
            WHERE id = ?
            """,
            (ruta_destino, 1 if usuario_modifico else 0, doc_id),
        )
        conn.commit()
        conn.close()
    
    def rechazar_documento(self, doc_id, motivo):
        """Rechazar"""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE pending_documents SET status = 'rejected', motivo_rechazo = ? WHERE id = ?",
            (motivo, doc_id),
        )
        conn.commit()
        conn.close()
    
    def registrar_log(self, nivel, origen, mensaje, doc_id=None):
        """Log"""
        print(f"[{nivel.upper()}] {origen}: {mensaje}")
