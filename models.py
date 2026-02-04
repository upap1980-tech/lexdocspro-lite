from flask_sqlalchemy import SQLAlchemy
from config import DB_PATH
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(120), nullable=False)
    role = db.Column(db.String(20), default='abogado')  # admin, abogado, asistente
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Expediente(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nombre_cliente = db.Column(db.String(200), nullable=False)
    numero = db.Column(db.String(50))
    path = db.Column(db.String(500), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))

class Documento(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    expediente_id = db.Column(db.Integer, db.ForeignKey('expediente.id'))
    nombre = db.Column(db.String(200), nullable=False)
    tipo = db.Column(db.String(100))  # demanda, burofax, etc.
    path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
