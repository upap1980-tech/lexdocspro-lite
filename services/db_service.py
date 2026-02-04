import os
import sqlite3
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "..", "lexdocs.db")

class DatabaseService:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(os.path.abspath(db_path)), exist_ok=True)
        self._init_db()

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_db(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("""
        CREATE TABLE IF NOT EXISTS documentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            archivo_original TEXT,
            ruta_temporal TEXT,
            cliente_codigo TEXT,
            cliente_detectado TEXT,
            tipo_documento TEXT,
            fecha_documento TEXT,
            estado TEXT,
            ruta_definitiva TEXT,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        cur.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nivel TEXT,
            origen TEXT,
            mensaje TEXT,
            documento_id INTEGER,
            creado_en TEXT DEFAULT CURRENT_TIMESTAMP
        );
        """)
        conn.commit()
        conn.close()

    def registrar_log(self, nivel, origen, mensaje, documento_id=None):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO logs (nivel, origen, mensaje, documento_id) VALUES (?, ?, ?, ?)",
            (nivel, origen, mensaje, documento_id),
        )
        conn.commit()
        conn.close()

    # Métodos usados por los endpoints de Fase 2 (stubs seguros):

    def obtener_estadisticas_hoy(self):
        conn = self._get_conn()
        cur = conn.cursor()
        hoy = datetime.now().date().isoformat()
        cur.execute("SELECT COUNT(*) FROM documentos WHERE date(creado_en)=?", (hoy,))
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documentos WHERE estado='auto'")
        automaticos = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documentos WHERE estado='revision'")
        en_revision = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM documentos WHERE estado='error'")
        errores = cur.fetchone()[0]
        conn.close()
        return {
            "total_hoy": total,
            "automaticos": automaticos,
            "en_revision": en_revision,
            "errores": errores,
        }

    def obtener_cola_revision(self):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM documentos WHERE estado='revision' ORDER BY creado_en DESC")
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        conn.close()
        return rows

    def obtener_procesados_hoy(self):
        conn = self._get_conn()
        cur = conn.cursor()
        hoy = datetime.now().date().isoformat()
        cur.execute(
            "SELECT * FROM documentos WHERE date(creado_en)=? ORDER BY creado_en DESC",
            (hoy,),
        )
        cols = [c[0] for c in cur.description]
        rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        conn.close()
        return rows

    def obtener_documento(self, doc_id: int):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM documentos WHERE id=?", (doc_id,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return None
        cols = [c[0] for c in cur.description]
        conn.close()
        return dict(zip(cols, row))

    def actualizar_documento(self, doc_id: int, updates: dict):
        if not updates:
            return
        conn = self._get_conn()
        cur = conn.cursor()
        sets = ", ".join([f"{k}=?" for k in updates.keys()])
        values = list(updates.values()) + [doc_id]
        cur.execute(f"UPDATE documentos SET {sets} WHERE id=?", values)
        conn.commit()
        conn.close()

    def aprobar_documento(self, doc_id: int, ruta_definitiva: str, usuario_modifico: bool):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE documentos SET estado='auto', ruta_definitiva=? WHERE id=?",
            (ruta_definitiva, doc_id),
        )
        conn.commit()
        conn.close()

    def rechazar_documento(self, doc_id: int, motivo: str):
        conn = self._get_conn()
        cur = conn.cursor()
        cur.execute(
            "UPDATE documentos SET estado='rechazado' WHERE id=?",
            (doc_id,),
        )
        conn.commit()
        conn.close()
