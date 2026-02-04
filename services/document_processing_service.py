import os
import shutil
from datetime import datetime
from werkzeug.utils import secure_filename

class DocumentProcessingService:
    def __init__(self, ocr_service, ai_service, base_dir):
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        self.base_dir = base_dir
        self.upload_folder = os.path.join(base_dir, "_UPLOADS")
        os.makedirs(self.upload_folder, exist_ok=True)

    def process_upload(self, file_storage, client="GENERAL", save_to_db=True):
        """
        Procesar archivo subido:
        1. Guardar temporalmente
        2. OCR
        3. (Opcional) Guardar en BD
        """
        filename = secure_filename(file_storage.filename)
        # Carpeta por cliente/año
        year = datetime.now().year
        client_dir = os.path.join(self.base_dir, str(year), client)
        os.makedirs(client_dir, exist_ok=True)
        
        file_path = os.path.join(client_dir, filename)
        
        # Evitar sobrescribir
        if os.path.exists(file_path):
            base, ext = os.path.splitext(filename)
            file_path = os.path.join(client_dir, f"{base}_{int(datetime.now().timestamp())}{ext}")
            
        file_storage.save(file_path)
        
        # Ejecutar OCR
        ocr_result = self.ocr_service.extraer_texto(file_path)
        
        # Guardar en BD si se solicita
        if save_to_db:
             from models import DatabaseManager
             db = DatabaseManager()
             conn = db.get_connection()
             try:
                 cursor = conn.cursor()
                 cursor.execute('''
                    INSERT INTO saved_documents (filename, file_path, client_name, doc_type, year)
                    VALUES (?, ?, ?, ?, ?)
                 ''', (os.path.basename(file_path), file_path, client, 'PENDIENTE_CLASIFICAR', year))
                 conn.commit()
                 doc_id = cursor.lastrowid
             finally:
                 conn.close()
                 
             return {
                 'success': True,
                 'doc_id': doc_id,
                 'text': ocr_result.get('texto', ''),
                 'path': file_path
             }
             
        return {
             'success': True,
             'text': ocr_result.get('texto', ''),
             'path': file_path
        }
