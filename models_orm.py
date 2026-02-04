from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False, default='abogado')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SavedDocument(db.Model):
    __tablename__ = 'saved_documents'
    
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=False)
    client_name = db.Column(db.String(100))
    doc_type = db.Column(db.String(50))
    year = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'filename': self.filename,
            'client_name': self.client_name,
            'doc_type': self.doc_type,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M')
        }
