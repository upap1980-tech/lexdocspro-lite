try:
    from flask_sqlalchemy import SQLAlchemy
    HAS_SQLALCHEMY = True
except ImportError:
    HAS_SQLALCHEMY = False

    class SQLAlchemy:  # Fallback P0 para evitar fallo de importación
        class _Type:
            def __init__(self, *args, **kwargs):
                del args, kwargs

        class Model:
            pass

        Integer = String = DateTime = _Type

        def __init__(self):
            self.Model = SQLAlchemy.Model

        def init_app(self, app):
            del app

        def Column(self, *args, **kwargs):
            del args, kwargs
            return None

from datetime import datetime
import sqlite3
import json
from config import DB_PATH

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    email = db.Column(db.String(120))
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class DatabaseManager:
    def __init__(self, app):
        self.app = app
        self.db = db
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        db.init_app(app)
    
    def init_db(self):
        with self.app.app_context():
            db.create_all()

    def get_connection(self):
        conn = sqlite3.connect(str(DB_PATH))
        conn.row_factory = sqlite3.Row
        return conn

    
    def count_documents_today(self):
        """Contar documentos guardados hoy"""
        from datetime import date
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            "SELECT COUNT(*) FROM saved_documents WHERE DATE(created_at) = ?",
            (date.today().isoformat(),),
        )
        result = cur.fetchone()[0] or 0
        conn.close()
        return result
    
    def count_pending_documents(self):
        """Contar documentos pendientes"""
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM pending_documents WHERE status = 'pending'")
        result = cur.fetchone()[0] or 0
        conn.close()
        return result

    def create_saved_document(
        self,
        filename,
        file_path,
        client_name=None,
        doc_type=None,
        doc_date=None,
        expedient=None,
        court=None,
        year=None,
        created_by=None,
    ):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO saved_documents
            (filename, file_path, client_name, doc_type, doc_date, expedient, court, year, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                filename,
                file_path,
                client_name,
                doc_type,
                doc_date,
                expedient,
                court,
                year,
                created_by,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        doc_id = cur.lastrowid
        conn.close()
        return doc_id

    def create_pending_document(
        self,
        temp_file_path,
        original_filename,
        extracted_data=None,
        proposed_data=None,
        status="proposed",
    ):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO pending_documents
            (temp_file_path, original_filename, extracted_data, proposed_data, status, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                temp_file_path,
                original_filename,
                json.dumps(extracted_data or {}, ensure_ascii=False),
                json.dumps(proposed_data or {}, ensure_ascii=False),
                status,
                datetime.now().isoformat(),
            ),
        )
        conn.commit()
        pending_id = cur.lastrowid
        conn.close()
        return pending_id

    def get_pending_document(self, pending_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM pending_documents WHERE id = ?", (pending_id,))
        row = cur.fetchone()
        conn.close()
        if not row:
            return None

        data = dict(row)
        for json_field in ("extracted_data", "proposed_data"):
            raw = data.get(json_field)
            if isinstance(raw, str) and raw:
                try:
                    data[json_field] = json.loads(raw)
                except Exception:
                    data[json_field] = {}
            elif raw is None:
                data[json_field] = {}
        return data

    def mark_pending_document_confirmed(self, pending_id, processed_by=None):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE pending_documents
            SET status = 'confirmed', processed_at = ?, processed_by = ?
            WHERE id = ?
            """,
            (datetime.now().isoformat(), processed_by, pending_id),
        )
        conn.commit()
        conn.close()

    def list_saved_documents(self, limit=50, offset=0):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            SELECT * FROM saved_documents
            ORDER BY datetime(created_at) DESC
            LIMIT ? OFFSET ?
            """,
            (int(limit), int(offset)),
        )
        rows = [dict(r) for r in cur.fetchall()]
        conn.close()
        return rows

    def get_user_by_id(self, user_id):
        conn = self.get_connection()
        cur = conn.cursor()
        # Compatibilidad con tablas user/users
        for table in ("users", "user"):
            try:
                cur.execute(f"SELECT * FROM {table} WHERE id = ?", (user_id,))
                row = cur.fetchone()
                if row:
                    conn.close()
                    return dict(row)
            except Exception:
                continue
        conn.close()
        return None

    def get_saved_document(self, doc_id):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM saved_documents WHERE id = ?", (doc_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None

    def add_case_note(self, expediente_id, contenido, tipo='nota', score=0):
        conn = self.get_connection()
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO case_notes (expediente_id, contenido, tipo, score, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (expediente_id, contenido, tipo, score, datetime.now().isoformat()),
        )
        conn.commit()
        note_id = cur.lastrowid
        conn.close()
        return note_id

    def registrar_log(self, level, source, message):
        conn = self.get_connection()
        cur = conn.cursor()
        try:
            cur.execute(
                """
                INSERT INTO logs (nivel, origen, mensaje, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (level, source, message, datetime.now().isoformat()),
            )
            conn.commit()
        except Exception:
            # Mantener robustez si la estructura de logs no coincide
            pass
        finally:
            conn.close()
