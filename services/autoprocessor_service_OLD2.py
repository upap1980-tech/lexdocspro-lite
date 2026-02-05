#!/usr/bin/env python3
"""
Auto-Processor Service - Watchdog automático para procesamiento de documentos
Versión Enterprise v3.2
"""
import os
import time
import threading
from datetime import datetime
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

class AutoProcessorService:
    def __init__(self, watch_dir, ocr_service=None, ai_service=None):
        """
        Inicializar servicio de auto-procesamiento
        
        Args:
            watch_dir: Directorio a monitorear
            ocr_service: Servicio OCR (opcional)
            ai_service: Servicio IA (opcional)
        """
        self.watch_dir = Path(watch_dir)
        self.watch_dir.mkdir(parents=True, exist_ok=True)
        
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        
        self.observer = None
        self.is_running = False
        
        # Estadísticas
        self.stats = {
            'processed': 0,
            'errors': 0,
            'pending': 0,
            'last_processed': None,
            'start_time': None
        }
        
        # Cola de procesamiento
        self.processing_queue = []
        self.processing_lock = threading.Lock()
        
        print(f"🤖 AutoProcessor inicializado en: {self.watch_dir}")
    
    def start(self):
        """Iniciar el watchdog"""
        if self.is_running:
            print("⚠️  AutoProcessor ya está corriendo")
            return False
        
        try:
            # Crear handler
            event_handler = DocumentHandler(self)
            
            # Crear observer
            self.observer = Observer()
            self.observer.schedule(event_handler, str(self.watch_dir), recursive=True)
            
            # Iniciar
            self.observer.start()
            self.is_running = True
            self.stats['start_time'] = datetime.now().isoformat()
            
            print(f"✅ AutoProcessor iniciado - Monitoreando: {self.watch_dir}")
            return True
            
        except Exception as e:
            print(f"❌ Error iniciando AutoProcessor: {e}")
            return False
    
    def stop(self):
        """Detener el watchdog"""
        if not self.is_running:
            return False
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
            
            self.is_running = False
            print("🛑 AutoProcessor detenido")
            return True
            
        except Exception as e:
            print(f"❌ Error deteniendo AutoProcessor: {e}")
            return False
    
    def process_file(self, file_path):
        """
        Procesar un archivo nuevo
        
        Args:
            file_path: Ruta del archivo a procesar
        """
        try:
            file_path = Path(file_path)
            
            # Verificar que sea PDF o imagen
            if file_path.suffix.lower() not in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
                print(f"⏭️  Archivo ignorado (tipo no soportado): {file_path.name}")
                return
            
            print(f"📄 Procesando: {file_path.name}")
            
            # Añadir a cola
            with self.processing_lock:
                self.processing_queue.append({
                    'file': str(file_path),
                    'status': 'pending',
                    'added_at': datetime.now().isoformat()
                })
                self.stats['pending'] = len(self.processing_queue)
            
            # Simular procesamiento (en producción: OCR + IA real)
            time.sleep(1)
            
            # OCR (si está disponible)
            ocr_text = None
            if self.ocr_service:
                try:
                    ocr_result = self.ocr_service.extract_text(str(file_path))
                    ocr_text = ocr_result.get('text', '')
                    print(f"  ✅ OCR: {len(ocr_text)} caracteres extraídos")
                except Exception as e:
                    print(f"  ⚠️  OCR error: {e}")
            
            # Análisis IA (si está disponible)
            if self.ai_service and ocr_text:
                try:
                    analysis = self.ai_service.analyze_document(ocr_text)
                    print(f"  ✅ IA: {analysis.get('doc_type', 'unknown')}")
                except Exception as e:
                    print(f"  ⚠️  IA error: {e}")
            
            # Mover a carpeta procesados
            processed_dir = self.watch_dir.parent / "PROCESADOS"
            processed_dir.mkdir(exist_ok=True)
            
            dest_path = processed_dir / file_path.name
            
            # Si ya existe, añadir timestamp
            if dest_path.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                dest_path = processed_dir / f"{file_path.stem}_{timestamp}{file_path.suffix}"
            
            file_path.rename(dest_path)
            
            # Actualizar estadísticas
            with self.processing_lock:
                self.stats['processed'] += 1
                self.stats['last_processed'] = file_path.name
                self.stats['pending'] -= 1
                
                # Remover de cola
                self.processing_queue = [
                    item for item in self.processing_queue 
                    if item['file'] != str(file_path)
                ]
            
            print(f"  ✅ Movido a: {dest_path}")
            
        except Exception as e:
            print(f"❌ Error procesando {file_path}: {e}")
            with self.processing_lock:
                self.stats['errors'] += 1
                self.stats['pending'] -= 1
    
    def get_status(self):
        """Obtener estado actual del servicio"""
        with self.processing_lock:
            return {
                'running': self.is_running,
                'watch_dir': str(self.watch_dir),
                'stats': self.stats.copy(),
                'queue': len(self.processing_queue),
                'queue_items': self.processing_queue.copy()
            }
    
    def scan_existing_files(self):
        """Escanear archivos existentes en la carpeta"""
        if not self.watch_dir.exists():
            return []
        
        files = []
        for ext in ['.pdf', '.png', '.jpg', '.jpeg', '.tiff']:
            files.extend(self.watch_dir.glob(f'*{ext}'))
            files.extend(self.watch_dir.glob(f'*{ext.upper()}'))
        
        return files


class DocumentHandler(FileSystemEventHandler):
    """Handler para eventos del sistema de archivos"""
    
    def __init__(self, processor):
        self.processor = processor
        super().__init__()
    
    def on_created(self, event):
        """Archivo creado"""
        if event.is_directory:
            return
        
        # Esperar a que el archivo se termine de escribir
        time.sleep(2)
        
        # Procesar en thread separado para no bloquear el watchdog
        thread = threading.Thread(
            target=self.processor.process_file,
            args=(event.src_path,)
        )
        thread.daemon = True
        thread.start()
    
    def on_modified(self, event):
        """Archivo modificado - ignorar por ahora"""
        pass

