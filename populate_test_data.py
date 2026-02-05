#!/usr/bin/env python3
"""
Añadir datos de prueba para ver el dashboard con números reales
"""
import json
import sqlite3
from datetime import date
from config import DB_PATH

conn = sqlite3.connect(str(DB_PATH))
cursor = conn.cursor()

print("📝 Añadiendo datos de prueba...")

# 1. Documentos guardados HOY
today = date.today().isoformat()
for i in range(5):
    cursor.execute("""
        INSERT INTO saved_documents 
        (filename, file_path, doc_type, client_name, doc_date, year, created_at) 
        VALUES (?, ?, 'contrato', 'Cliente Test', ?, ?, ?)
    """, (f'documento_test_{i}.pdf', f'/test/doc{i}.pdf', today, date.today().year, today))

print(f"✅ Añadidos 5 documentos procesados hoy")

# 2. Documentos pendientes
for i in range(3):
    extracted_data = {
        "client": "Cliente Test",
        "doc_type": "notificacion",
        "date": today,
        "confidence": 84
    }
    cursor.execute("""
        INSERT INTO pending_documents 
        (temp_file_path, original_filename, extracted_data, status, created_at) 
        VALUES (?, ?, ?, 'pending', ?)
    """, (f'/tmp/pendiente_{i}.pdf', f'pendiente_{i}.pdf', json.dumps(extracted_data), today))

print(f"✅ Añadidos 3 documentos en revisión")

# 3. Documento rechazado (error)
cursor.execute("""
    INSERT INTO pending_documents 
    (temp_file_path, original_filename, extracted_data, status, created_at) 
    VALUES ('/tmp/error_test.pdf', 'error_test.pdf', ?, 'rejected', ?)
""", (json.dumps({"error": "Documento de prueba rechazado"}), today))

print(f"✅ Añadido 1 error")

# 4. Alertas LexNET urgentes
for i in range(2):
    cursor.execute("""
        INSERT INTO notifications 
        (type, title, body, urgency, read, created_at, notification_date, deadline_days, case_type, resolution_type, parties_json) 
        VALUES ('lexnet', ?, 'Notificación urgente de prueba', 'CRITICAL', 0, ?, ?, 3, 'civil', 'providencia', ?)
    """, (
        f'Alerta Test {i+1}',
        today,
        today,
        json.dumps({"actor": "Cliente Test", "demandado": "Contraparte Demo"})
    ))

print(f"✅ Añadidas 2 alertas críticas")

conn.commit()
conn.close()

print("")
print("✅ Datos de prueba añadidos correctamente")
print("🔄 Recarga el navegador para ver los nuevos números")
