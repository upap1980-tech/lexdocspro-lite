"""
Auth Service - Gestión básica de usuarios y autenticación
"""
from __future__ import annotations

import sqlite3
from datetime import datetime
from typing import Optional

from werkzeug.security import generate_password_hash, check_password_hash

from config import DB_PATH


class AuthDB:
    def __init__(self):
        self.db_path = str(DB_PATH)

    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def log_action(self, user_id: int, action: str, ip_address: Optional[str] = None):
        try:
            conn = self._connect()
            cur = conn.cursor()
            cur.execute(
                """
                INSERT INTO audit_log (user_id, action, ip_address, created_at)
                VALUES (?, ?, ?, ?)
                """,
                (user_id, action, ip_address, datetime.now().isoformat()),
            )
            conn.commit()
            conn.close()
        except Exception:
            pass

    def add_to_blacklist(self, jti: str):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO token_blacklist (jti, created_at) VALUES (?, ?)",
            (jti, datetime.now().isoformat()),
        )
        conn.commit()
        conn.close()

    def get_user_by_id(self, user_id: int):
        conn = self._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cur.fetchone()
        conn.close()
        return dict(row) if row else None


class AuthService:
    def __init__(self, db: AuthDB):
        self.db = db

    def register_user(self, email, password, rol="LECTURA", nombre=None):
        if not email or not password:
            return {"success": False, "error": "email y password requeridos"}
        conn = self.db._connect()
        cur = conn.cursor()
        cur.execute("SELECT id FROM users WHERE email = ?", (email,))
        if cur.fetchone():
            conn.close()
            return {"success": False, "error": "Usuario ya existe"}
        pwd_hash = generate_password_hash(password)
        cur.execute(
            """
            INSERT INTO users (email, password_hash, rol, nombre, activo, created_at)
            VALUES (?, ?, ?, ?, 1, ?)
            """,
            (email, pwd_hash, rol, nombre, datetime.now().isoformat()),
        )
        conn.commit()
        user_id = cur.lastrowid
        conn.close()
        return {"success": True, "user_id": user_id, "message": "Usuario registrado"}

    def authenticate(self, email, password):
        conn = self.db._connect()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = ?", (email,))
        row = cur.fetchone()
        if not row:
            conn.close()
            return {"success": False, "error": "Credenciales inválidas"}
        user = dict(row)
        if not user.get("activo", 1):
            conn.close()
            return {"success": False, "error": "Usuario inactivo"}
        if not check_password_hash(user["password_hash"], password):
            conn.close()
            return {"success": False, "error": "Credenciales inválidas"}
        cur.execute("UPDATE users SET last_login = ? WHERE id = ?", (datetime.now().isoformat(), user["id"]))
        conn.commit()
        conn.close()
        return {"success": True, "user": user}

    def get_user_safe(self, user_id):
        user = self.db.get_user_by_id(user_id)
        if not user:
            return None
        user.pop("password_hash", None)
        return user
