import os
import re
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from werkzeug.utils import secure_filename
from config import DB_PATH

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
        ocr_text = self.ocr_service.extract_text(file_path)
        
        # Guardar en BD si se solicita
        if save_to_db:
            doc_id = None
            try:
                conn = sqlite3.connect(str(DB_PATH))
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO saved_documents (filename, file_path, client_name, doc_type, year, created_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    os.path.basename(file_path),
                    file_path,
                    client,
                    'PENDIENTE_CLASIFICAR',
                    year,
                    datetime.now().isoformat()
                ))
                conn.commit()
                doc_id = cursor.lastrowid
                conn.close()
            except Exception:
                doc_id = None
            
            return {
                'success': True,
                'doc_id': doc_id,
                'text': ocr_text or '',
                'path': file_path
            }
             
        return {
            'success': True,
            'text': ocr_text or '',
            'path': file_path
        }

    def extract_metadata(self, temp_file_path, hint_year=None):
        """Extraer metadata básica para propuesta de guardado."""
        if not temp_file_path or not os.path.exists(temp_file_path):
            return {'success': False, 'error': 'temp_file_path inválido'}

        text = self.ocr_service.extract_text(temp_file_path)
        text_l = (text or '').lower()

        detected_type = 'documento'
        type_map = {
            'demanda': 'demanda',
            'sentencia': 'sentencia',
            'auto': 'auto',
            'decreto': 'decreto',
            'providencia': 'providencia',
            'lexnet': 'notificacion_lexnet',
        }
        for key, value in type_map.items():
            if key in text_l:
                detected_type = value
                break

        date_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](20\d{2})', text or '')
        if date_match:
            date_iso = f"{date_match.group(3)}-{date_match.group(2).zfill(2)}-{date_match.group(1).zfill(2)}"
            year = int(date_match.group(3))
        else:
            year = int(hint_year or datetime.now().year)
            date_iso = f"{year}-01-01"

        # Heurística simple de cliente
        client = "SIN_CLASIFICAR"
        client_match = re.search(
            r'(DEMANDANTE|DEMANDADO|CLIENTE|IMPUTADO)[:\s]+([A-ZÁÉÍÓÚÑ][A-Za-zÁÉÍÓÚÑáéíóúñ\s]{4,60})',
            text or '',
            re.IGNORECASE
        )
        if client_match:
            client = client_match.group(2).strip()

        metadata = {
            'client': client,
            'doc_type': detected_type,
            'date': date_iso,
            'expedient': '',
            'court': '',
            'year': year,
            'confidence': 70
        }
        return {'success': True, 'metadata': metadata, 'text_preview': (text or '')[:1000]}

    def propose_save(self, temp_file_path, extracted_data):
        """Proponer ruta y nombre final con base en metadata."""
        if not temp_file_path or not os.path.exists(temp_file_path):
            return {'success': False, 'error': 'temp_file_path inválido'}

        data = extracted_data or {}
        year = int(data.get('year') or datetime.now().year)
        client = secure_filename(data.get('client') or 'SIN_CLASIFICAR') or 'SIN_CLASIFICAR'
        doc_type = secure_filename(data.get('doc_type') or 'documento') or 'documento'
        date_iso = data.get('date') or f"{year}-01-01"

        ext = os.path.splitext(temp_file_path)[1].lower() or '.pdf'
        folder = os.path.join(self.base_dir, str(year), client)
        filename = f"{date_iso}_{doc_type}{ext}"
        final_path = os.path.join(folder, filename)

        return {
            'success': True,
            'proposal': {
                'year': year,
                'client': data.get('client') or 'SIN_CLASIFICAR',
                'doc_type': data.get('doc_type') or 'documento',
                'date': date_iso,
                'path': folder,
                'filename': filename,
                'final_path': final_path
            }
        }

    def confirm_save(self, temp_file_path, confirmed_data, current_user_id=None):
        """Guardar definitivamente el documento en la ruta confirmada."""
        del current_user_id

        if not temp_file_path or not os.path.exists(temp_file_path):
            return {'success': False, 'error': 'temp_file_path inválido'}
        if not confirmed_data:
            return {'success': False, 'error': 'confirmed_data requerido'}

        folder = confirmed_data.get('path')
        filename = confirmed_data.get('filename')
        if not folder or not filename:
            return {'success': False, 'error': 'path y filename son requeridos'}

        # Seguridad: evitar guardados fuera de la base documental configurada.
        base_abs = os.path.abspath(self.base_dir)
        folder_abs = os.path.abspath(folder)
        if not folder_abs.startswith(base_abs):
            return {'success': False, 'error': 'path fuera de base documental permitida'}

        os.makedirs(folder_abs, exist_ok=True)
        safe_filename = secure_filename(filename)
        final_path = os.path.join(folder_abs, safe_filename)

        # Evitar sobreescritura accidental
        if os.path.exists(final_path):
            stem, ext = os.path.splitext(safe_filename)
            final_path = os.path.join(
                folder_abs,
                f"{stem}_{int(datetime.now().timestamp())}{ext}",
            )
        shutil.move(temp_file_path, final_path)

        return {'success': True, 'final_path': final_path}

    def get_path_options(self, year, client_filter=None):
        year_path = os.path.join(self.base_dir, str(year))
        if not os.path.isdir(year_path):
            return []

        folders = []
        filter_text = (client_filter or '').lower()
        for item in sorted(os.listdir(year_path)):
            full = os.path.join(year_path, item)
            if not os.path.isdir(full):
                continue
            if filter_text and filter_text not in item.lower():
                continue
            folders.append({'name': item, 'path': full})
        return folders

    def get_document_types(self):
        return [
            'demanda',
            'sentencia',
            'auto',
            'decreto',
            'providencia',
            'notificacion_lexnet',
            'contrato',
            'escrito',
            'otros'
        ]
