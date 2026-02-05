#!/usr/bin/env python3
"""
Auto-Processor Service v2.0 - CON BACKUP Y TRAZABILIDAD COMPLETA
REGLA DE ORO: NUNCA perder un archivo
"""
import os
import time
import shutil
import threading
import sqlite3
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AutoProcessorService:
    def __init__(self, watch_dir=None, ocr_service=None, ai_service=None):
        """Inicializar con sistema de backup y trazabilidad"""
        
        # Carpetas del sistema
        self.watch_dir = Path(watch_dir or Path.home() / "Desktop" / "PENDIENTES_LEXDOCS")
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        # NUEVA: Carpeta de BACKUP (copia de seguridad SIEMPRE)
        self.backup_dir = self.watch_dir.parent / "BACKUP_LEXDOCS"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Carpeta de procesados
        self.processed_dir = self.watch_dir.parent / "PROCESADOS"
        self.processed_dir.mkdir(parents=True, exist_ok=True)
        
        # Carpeta de errores
        self.error_dir = self.watch_dir.parent / "ERRORES_LEXDOCS"
        self.error_dir.mkdir(parents=True, exist_ok=True)
        
        # Base de datos de trazabilidad
        self.db_path = Path(__file__).parent.parent / "processing_log.db"
        self._init_database()
        
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        
        self.observer = None
        self.is_running = False
        
        self.stats = {
            'processed': 0,
            'errors': 0,
            'pending': 0,
            'last_processed': None,
            'start_time': None
        }
        
        self.processing_queue = []
        self.processing_lock = threading.Lock()
        
        print(f"🤖 AutoProcessor v2.0 inicializado")
        print(f"   📁 Monitoreo: {self.watch_dir}")
        print(f"   💾 Backup: {self.backup_dir}")
        print(f"   ✅ Procesados: {self.processed_dir}")
        print(f"   ❌ Errores: {self.error_dir}")
        print(f"   📊 Log BD: {self.db_path}")
    
    def _init_database(self):
        """Crear base de datos de trazabilidad"""
        conn = sqlite3.connect(str(self.db_path))
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS processing_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_path TEXT NOT NULL,
                backup_path TEXT NOT NULL,
                final_path TEXT,
                status TEXT NOT NULL,
                error_message TEXT,
                ocr_chars INTEGER,
                ai_analysis TEXT,
                processing_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        
        print(f"✅ Base de datos de trazabilidad lista")
    
    def _log_processing(self, filename, original_path, backup_path, status, 
                       final_path=None, error_message=None, ocr_chars=0, 
                       ai_analysis=None, processing_time=0):
        """Registrar procesamiento en BD"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO processing_log 
                (filename, original_path, backup_path, final_path, status, 
                 error_message, ocr_chars, ai_analysis, processing_time, completed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                filename,
                str(original_path),
                str(backup_path),
                str(final_path) if final_path else None,
                status,
                error_message,
                ocr_chars,
                ai_analysis,
                processing_time,
                datetime.now().isoformat()
            ))
            
            conn.commit()
            conn.close()
            
            print(f"📝 Log guardado: {filename} → {status}")
            
        except Exception as e:
            print(f"⚠️  Error guardando log: {e}")
    
    def start(self):
        """Iniciar watchdog"""
        if self.is_running:
            return False
        
        try:
            event_handler = DocumentHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.watch_dir), recursive=True)
            self.observer.start()
            
            self.is_running = True
            self.stats['start_time'] = datetime.now().isoformat()
            
            print(f"✅ AutoProcessor iniciado")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando: {e}")
            return False
    
    def stop(self):
        """Detener watchdog"""
        if not self.is_running:
            return False
        
        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5)
        
        self.is_running = False
        print("🛑 AutoProcessor detenido")
        return True
    
    def process_file(self, file_path):
        """
        Procesar archivo CON BACKUP y TRAZABILIDAD
        
        FLUJO:
        1. Verificar archivo válido
        2. CREAR BACKUP INMEDIATO (copia de seguridad)
        3. Registrar inicio en BD
        4. Procesar (OCR + IA)
        5. Mover a PROCESADOS o ERRORES
        6. Actualizar BD con resultado
        7. NUNCA eliminar backup
        """
        start_time = time.time()
        file_path = Path(file_path)
        
        try:
            # ═══════════════════════════════════════════════════════════
            # PASO 1: VERIFICACIONES
            # ═══════════════════════════════════════════════════════════
            if not file_path.exists():
                print(f"⚠️  Archivo no existe: {file_path}")
                return
            
            if file_path.suffix.lower() not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
                print(f"⏭️  Extensión no soportada: {file_path.suffix}")
                return
            
            print(f"\n{'='*70}")
            print(f"📄 PROCESANDO: {file_path.name}")
            print(f"{'='*70}")
            
            # ═══════════════════════════════════════════════════════════
            # PASO 2: BACKUP INMEDIATO (REGLA DE ORO)
            # ═══════════════════════════════════════════════════════════
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"{timestamp}_{file_path.name}"
            backup_path = self.backup_dir / backup_filename
            
            shutil.copy2(file_path, backup_path)
            print(f"💾 BACKUP CREADO: {backup_path.name}")
            
            # ═══════════════════════════════════════════════════════════
            # PASO 3: REGISTRAR INICIO
            # ═══════════════════════════════════════════════════════════
            with self.processing_lock:
                self.processing_queue.append({
                    'file': str(file_path),
                    'status': 'processing',
                    'added_at': datetime.now().isoformat(),
                    'backup': str(backup_path)
                })
                self.stats['pending'] = len(self.processing_queue)
            
            # ═══════════════════════════════════════════════════════════
            # PASO 4: PROCESAMIENTO (OCR + IA)
            # ═══════════════════════════════════════════════════════════
            ocr_chars = 0
            ai_analysis = None
            
            # OCR
            if self.ocr_service:
                try:
                    print("🔍 Ejecutando OCR...")
                    ocr_result = self.ocr_service.extract_text(str(file_path))
                    ocr_text = ocr_result.get('text', '')
                    ocr_chars = len(ocr_text)
                    print(f"   ✅ {ocr_chars} caracteres extraídos")
                except Exception as e:
                    print(f"   ⚠️  OCR error: {e}")
                    ocr_text = None
            
            # IA
            if self.ai_service and ocr_text:
                try:
                    print("🤖 Analizando con IA...")
                    analysis = self.ai_service.analyze_document(ocr_text)
                    ai_analysis = str(analysis.get('doc_type', 'unknown'))
                    print(f"   ✅ Tipo: {ai_analysis}")
                except Exception as e:
                    print(f"   ⚠️  IA error: {e}")
            
            # ═══════════════════════════════════════════════════════════
            # PASO 5: MOVER A PROCESADOS
            # ═══════════════════════════════════════════════════════════
            final_filename = f"{timestamp}_{file_path.name}"
            final_path = self.processed_dir / final_filename
            
            # Si existe, añadir sufijo
            counter = 1
            while final_path.exists():
                final_path = self.processed_dir / f"{timestamp}_{counter}_{file_path.name}"
                counter += 1
            
            shutil.move(str(file_path), str(final_path))
            print(f"✅ MOVIDO A: {final_path.name}")
            
            # ═══════════════════════════════════════════════════════════
            # PASO 6: REGISTRAR ÉXITO
            # ═══════════════════════════════════════════════════════════
            processing_time = time.time() - start_time
            
            self._log_processing(
                filename=file_path.name,
                original_path=file_path,
                backup_path=backup_path,
                final_path=final_path,
                status='SUCCESS',
                ocr_chars=ocr_chars,
                ai_analysis=ai_analysis,
                processing_time=processing_time
            )
            
            with self.processing_lock:
                self.stats['processed'] += 1
                self.stats['last_processed'] = file_path.name
                self.processing_queue = [
                    item for item in self.processing_queue 
                    if item['file'] != str(file_path)
                ]
                self.stats['pending'] = len(self.processing_queue)
            
            print(f"⏱️  Tiempo: {processing_time:.2f}s")
            print(f"{'='*70}\n")
            
        except Exception as e:
            # ═══════════════════════════════════════════════════════════
            # MANEJO DE ERRORES
            # ═══════════════════════════════════════════════════════════
            print(f"❌ ERROR: {e}")
            
            import traceback
            error_trace = traceback.format_exc()
            print(error_trace)
            
            # Mover a carpeta de errores
            try:
                error_filename = f"{timestamp}_ERROR_{file_path.name}"
                error_path = self.error_dir / error_filename
                
                if file_path.exists():
                    shutil.move(str(file_path), str(error_path))
                    print(f"🚨 MOVIDO A ERRORES: {error_path.name}")
                
                # Registrar error
                self._log_processing(
                    filename=file_path.name,
                    original_path=file_path,
                    backup_path=backup_path,
                    final_path=error_path,
                    status='ERROR',
                    error_message=f"{str(e)}\n{error_trace}",
                    processing_time=time.time() - start_time
                )
                
            except Exception as e2:
                print(f"❌ Error moviendo a carpeta errores: {e2}")
            
            with self.processing_lock:
                self.stats['errors'] += 1
                self.stats['pending'] = max(0, self.stats['pending'] - 1)
            
            print(f"{'='*70}\n")
    
    def get_status(self):
        """Obtener estado"""
        return {
            'running': self.is_running,
            'watch_dir': str(self.watch_dir),
            'backup_dir': str(self.backup_dir),
            'processed_dir': str(self.processed_dir),
            'error_dir': str(self.error_dir),
            'stats': self.stats.copy(),
            'queue': len(self.processing_queue),
            'queue_items': self.processing_queue.copy()
        }
    
    def get_processing_log(self, limit=50):
        """Obtener últimos registros del log"""
        try:
            conn = sqlite3.connect(str(self.db_path))
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filename, status, error_message, ocr_chars, 
                       ai_analysis, processing_time, completed_at,
                       backup_path, final_path
                FROM processing_log
                ORDER BY id DESC
                LIMIT ?
            ''', (limit,))
            
            rows = cursor.fetchall()
            conn.close()
            
            return [
                {
                    'filename': row[0],
                    'status': row[1],
                    'error': row[2],
                    'ocr_chars': row[3],
                    'ai_analysis': row[4],
                    'time': row[5],
                    'completed_at': row[6],
                    'backup_path': row[7],
                    'final_path': row[8]
                }
                for row in rows
            ]
            
        except Exception as e:
            print(f"Error leyendo log: {e}")
            return []
    
    def scan_existing_files(self):
        """Escanear archivos existentes"""
        if not self.watch_dir.exists():
            return []
        
        files = []
        for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
            files.extend(self.watch_dir.glob(f'*{ext}'))
            files.extend(self.watch_dir.glob(f'*{ext.upper()}'))
        
        return files


class DocumentHandler(FileSystemEventHandler):
    """Handler de eventos"""
    
    def __init__(self, processor):
        self.processor = processor
        super().__init__()
    
    def on_created(self, event):
        if event.is_directory:
            return
        
        # Esperar a que se termine de escribir
        time.sleep(2)
        
        # Procesar en thread separado
        thread = threading.Thread(
            target=self.processor.process_file,
            args=(event.src_path,)
        )
        thread.daemon = True
        thread.start()

