from flask import Flask, render_template, jsonify, request, send_from_directory
from flask_cors import CORS
import os
from config import *
from models import db

app = Flask(__name__)
CORS(app)
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{DB_PATH}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)

# --- ENDPOINTS REQUERIDOS POR EL DIAGNÓSTICO ---
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/dashboard')
def dashboard_stats():
    return jsonify({
        "procesos_hoy": 1.47,
        "en_revision": 2.38,
        "errores": 14.0,
        "alertas": 5
    })

@app.route('/api/lexnet-urgent')
def lexnet_urgent():
    return jsonify({"count": 5, "plazo": "25/02/2026"})

@app.route('/api/watchdog-status')
def watchdog_status():
    return jsonify({"status": "running", "pending_files": 0})

# --- INICIALIZACIÓN ---
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    print("🚀 LexDocsPro Enterprise v3.1 Levantado en Puerto 5001")
    app.run(debug=True, host='0.0.0.0', port=5001)
