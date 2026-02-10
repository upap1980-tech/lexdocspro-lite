#!/usr/bin/env python3
import sqlite3
import sys
from werkzeug.security import generate_password_hash

DB_PATH = 'lexdocs.db'
EMAIL = sys.argv[1] if len(sys.argv) > 1 else 'admin@lexdocs.com'
PASSWORD = sys.argv[2] if len(sys.argv) > 2 else 'admin123'
ROLE = sys.argv[3] if len(sys.argv) > 3 else 'ADMIN'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()
cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    rol TEXT NOT NULL DEFAULT 'LECTURA',
    nombre TEXT,
    activo INTEGER NOT NULL DEFAULT 1,
    created_at TEXT,
    last_login TEXT
)
""")

pwd_hash = generate_password_hash(PASSWORD)
cur.execute("SELECT id FROM users WHERE email = ?", (EMAIL,))
row = cur.fetchone()
if row:
    cur.execute(
        "UPDATE users SET password_hash = ?, rol = ?, activo = 1 WHERE email = ?",
        (pwd_hash, ROLE, EMAIL),
    )
    action = 'updated'
else:
    cur.execute(
        "INSERT INTO users (email, password_hash, rol, nombre, activo, created_at) VALUES (?, ?, ?, ?, 1, datetime('now'))",
        (EMAIL, pwd_hash, ROLE, 'Administrador'),
    )
    action = 'created'

conn.commit()
conn.close()
print(f"OK: {action} user {EMAIL} with role {ROLE}")
