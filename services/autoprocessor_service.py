"""
Auto-Processor Service - Monitor de carpeta PENDIENTES_LEXDOCS
Procesa automáticamente PDFs/imágenes: OCR → IA → Clasificación → Move
"""
import os
import time
import shutil
from datetime import datetime
from pathlib import Path
from threading import Thread, Event
from typing import Optional, Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from services.ocr_service import OCRService
from services.ai_service import AIService
import json
import re

class AutoProcessorService:
    """Servicio de procesamiento automático de documentos"""
    
    def __init__(self, ocr_service: OCRService, ai_service: AIService):
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        self.is_running = False
        self.observer = None
        self.stats = {
            'processed': 0,
            'errors': 0,
            'last_processed': None
        }
        self.logs = []
        self.max_logs = 100
        
        # Configuración de carpetas y persistencia
        self.watch_folder = os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS")
        self.dest_folder = os.path.expanduser("~/Desktop/EXPEDIENTES")
        self.state_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'auto_processor_state.json')
        
        # Cargar estado previo
        self._load_state()
        
        # Crear carpetas si no existen
        os.makedirs(self.watch_folder, exist_ok=True)
        os.makedirs(self.dest_folder, exist_ok=True)
        
        print(f"📁 Auto-Processor PRO v2.3 configurado:")
        print(f"   Watch: {self.watch_folder}")
        print(f"   Destino: {self.dest_folder}")
        print(f"   Estado: {self.state_file}")

    def _load_state(self):
        """Cargar estado persistente de procesamiento"""
        self.processed_files = set()
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r') as f:
                    state = json.load(f)
                    self.processed_files = set(state.get('processed_files', []))
                    self.stats.update(state.get('stats', {}))
                    self.add_log("INFO", f"Estado cargado: {len(self.processed_files)} archivos procesados anteriormente")
            except Exception as e:
                self.add_log("ERROR", f"Error cargando estado: {e}")

    def _save_state(self):
        """Guardar estado persistente"""
        try:
            state = {
                'processed_files': list(self.processed_files),
                'stats': self.stats,
                'last_save': datetime.now().isoformat()
            }
            with open(self.state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            print(f"❌ Error guardando estado auto-processor: {e}")
    
    def start(self):
        """Iniciar monitoreo de carpeta"""
        if self.is_running:
            return {"success": False, "error": "Auto-processor ya está corriendo"}
        
        try:
            event_handler = DocumentEventHandler(self)
            self.observer = Observer()
            self.observer.schedule(event_handler, self.watch_folder, recursive=False)
            self.observer.start()
            self.is_running = True
            
            self.add_log("INFO", f"Auto-processor iniciado. Monitoreando: {self.watch_folder}")
            
            return {
                "success": True,
                "message": "Auto-processor iniciado",
                "watching": self.watch_folder
            }
        except Exception as e:
            self.add_log("ERROR", f"Error al iniciar: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def stop(self):
        """Detener monitoreo"""
        if not self.is_running:
            return {"success": False, "error": "Auto-processor no está corriendo"}
        
        try:
            if self.observer:
                self.observer.stop()
                self.observer.join(timeout=5)
                self.observer = None
            
            self.is_running = False
            self.add_log("INFO", "Auto-processor detenido")
            
            return {"success": True, "message": "Auto-processor detenido"}
        except Exception as e:
            self.add_log("ERROR", f"Error al detener: {str(e)}")
            return {"success": False, "error": str(e)}
    
    def get_status(self) -> Dict:
        """Obtener estado actual"""
        return {
            "running": self.is_running,
            "stats": self.stats,
            "watching": self.watch_folder if self.is_running else None,
            "destination": self.dest_folder
        }
    
    def get_logs(self, limit: int = 50) -> list:
        """Obtener logs recientes"""
        return self.logs[-limit:]
    
    def add_log(self, level: str, message: str):
        """Añadir entrada al log"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message
        }
        self.logs.append(log_entry)
        
        # Limitar tamaño de logs
        if len(self.logs) > self.max_logs:
            self.logs = self.logs[-self.max_logs:]
        
        # Print to console
        print(f"[{level}] {message}")
    
    def process_file(self, file_path: str):
        """Procesar archivo detectado (v2.3 PRO)"""
        try:
            file_path = Path(file_path)
            file_name = file_path.name
            
            # 0. Verificar si ya fue procesado (persistente)
            if file_name in self.processed_files:
                self.add_log("INFO", f"⏩ Saltando (ya procesado): {file_name}")
                return

            # Verificar que el archivo aún existe
            if not file_path.exists():
                return
            
            # Verificar que es un archivo soportado
            if not self.ocr_service.is_supported_file(file_name):
                self.add_log("WARNING", f"Archivo no soportado: {file_name}")
                return
            
            self.add_log("INFO", f"🔄 Procesando PRO: {file_name}")
            
            # 1. Extraer texto con OCR
            self.add_log("INFO", f"📄 Extrayendo texto...")
            text = self.ocr_service.extract_text(str(file_path))
            
            if not text or len(text) < 20:
                self.add_log("WARNING", f"Poco texto extraído de {file_path.name}")
                self.stats['errors'] += 1
                return
            
            # 2. Analizar con IA
            self.add_log("INFO", f"🤖 Analizando con IA...")
            metadata = self._analyze_with_ai(text[:3000])  # Limitar a 3000 chars
            
            # 3. Clasificar y mover
            dest_path = self._classify_and_move(file_path, metadata)
            
            if dest_path:
                self.stats['processed'] += 1
                self.stats['last_processed'] = datetime.now().isoformat()
                
                # Marcar como procesado y guardar estado
                self.processed_files.add(file_name)
                self._save_state()
                
                self.add_log("SUCCESS", f"✅ Procesado: {file_name} → {dest_path}")
            else:
                self.stats['errors'] += 1
                self.add_log("ERROR", f"❌ Error al mover: {file_path.name}")
        
        except Exception as e:
            self.stats['errors'] += 1
            self.add_log("ERROR", f"❌ Error procesando {file_path.name}: {str(e)}")
    
    def _analyze_with_ai(self, text: str) -> Dict:
        """Analizar texto con IA para extraer metadata"""
        try:
            prompt_sistema = """Eres un experto en clasificación de documentos legales españoles.
Extrae información estructurada en formato JSON."""
            
            prompt_usuario = f"""Analiza este documento legal y extrae:

DOCUMENTO:
{text}

Responde SOLO con JSON:
{{
  "cliente": "nombre del cliente (no abogado)",
  "tipo_documento": "tipo (ej: contrato, demanda, notificacion)",
  "fecha": "dd/mm/aaaa si aparece",
  "ano": "aaaa"
}}"""
            
            # Usar sistema de cascada (v2.3.0)
            result = self.ai_service.chat_cascade(
                prompt=prompt_usuario,
                context=prompt_sistema,
                mode='standard'
            )
            
            if result.get('success'):
                response = result.get('response', '')
                # Extraer JSON de la respuesta
                json_match = re.search(r'\{[^{}]*\}', response, re.DOTALL)
                if json_match:
                    metadata = json.loads(json_match.group())
                    print(f"✅ IA ({result.get('provider')}) procesó archivo")
                    return metadata
            
            # Fallback a valores por defecto
            return {
                "cliente": "SIN_CLASIFICAR",
                "tipo_documento": "documento",
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "ano": str(datetime.now().year)
            }
        
        except Exception as e:
            print(f"Error en análisis IA: {e}")
            return {
                "cliente": "ERROR",
                "tipo_documento": "documento",
                "fecha": datetime.now().strftime("%d/%m/%Y"),
                "ano": str(datetime.now().year)
            }
    
    def _classify_and_move(self, file_path: Path, metadata: Dict) -> Optional[str]:
        """Clasificar y mover archivo a carpeta destino"""
        try:
            # Sanitizar nombre de cliente
            cliente = metadata.get('cliente', 'SIN_CLASIFICAR')
            cliente = re.sub(r'[^\w\s-]', '', cliente).strip()
            cliente = re.sub(r'[-\s]+', '_', cliente)
            
            # Obtener año
            ano = metadata.get('ano', str(datetime.now().year))
            
            # Crear estructura de carpetas
            year_folder = os.path.join(self.dest_folder, ano)
            
            # Buscar carpeta de cliente existente o crear nueva
            client_folder = self._find_or_create_client_folder(year_folder, cliente, ano)
            
            # Generar nombre de archivo
            tipo = metadata.get('tipo_documento', 'documento').replace(' ', '_')
            fecha = metadata.get('fecha', '').replace('/', '-') or datetime.now().strftime('%Y-%m-%d')
            ext = file_path.suffix
            new_filename = f"{fecha}_{tipo}{ext}"
            
            # Ruta destino
            dest_path = os.path.join(client_folder, new_filename)
            
            # Si ya existe, añadir timestamp
            if os.path.exists(dest_path):
                timestamp = datetime.now().strftime("%H%M%S")
                new_filename = f"{fecha}_{tipo}_{timestamp}{ext}"
                dest_path = os.path.join(client_folder, new_filename)
            
            # Mover archivo
            shutil.move(str(file_path), dest_path)
            
            # Retornar ruta relativa
            rel_path = os.path.relpath(dest_path, self.dest_folder)
            return rel_path
        
        except Exception as e:
            print(f"Error al clasificar y mover: {e}")
            return None
    
    def _find_or_create_client_folder(self, year_folder: str, cliente: str, ano: str) -> str:
        """Buscar carpeta de cliente existente o crear nueva"""
        os.makedirs(year_folder, exist_ok=True)
        
        # Buscar carpeta existente que contenga el nombre del cliente
        existing_folders = [f for f in os.listdir(year_folder) if os.path.isdir(os.path.join(year_folder, f))]
        
        for folder in existing_folders:
            if cliente.lower() in folder.lower():
                return os.path.join(year_folder, folder)
        
        # Crear nueva carpeta con código
        existing_codes = []
        for folder in existing_folders:
            match = re.match(r'(\d{4})-(\d{2})', folder)
            if match:
                existing_codes.append(int(match.group(2)))
        
        next_code = max(existing_codes, default=0) + 1
        folder_name = f"{ano}-{next_code:02d} {cliente}"
        client_folder = os.path.join(year_folder, folder_name)
        os.makedirs(client_folder, exist_ok=True)
        
        return client_folder


class DocumentEventHandler(FileSystemEventHandler):
    """Handler robusto para eventos de archivos (v2.3 PRO)"""
    
    def __init__(self, processor: AutoProcessorService):
        self.processor = processor
        self.processing = set() 
    
    def on_created(self, event):
        if event.is_directory: return
        self._handle_new_file(event.src_path)

    def on_moved(self, event):
        if event.is_directory: return
        self._handle_new_file(event.dest_path)

    def _handle_new_file(self, file_path):
        """Manejar nuevo archivo con reintentos para asegurar escritura completa"""
        if file_path in self.processing: return
        
        # Ignorar archivos temporales o de sistema
        file_name = Path(file_path).name
        if file_name.startswith('.') or file_name.startswith('~'):
            return

        self.processing.add(file_path)
        
        def wait_and_process():
            try:
                # Esperar a que el tamaño del archivo se estabilice
                last_size = -1
                retries = 15
                while retries > 0:
                    if not os.path.exists(file_path): return
                    
                    try:
                        current_size = os.path.getsize(file_path)
                        if current_size == last_size and current_size > 0:
                            # Intentar abrir el archivo para confirmar acceso real
                            with open(file_path, 'rb') as f:
                                break 
                    except (IOError, OSError):
                        pass # Sigue bloqueado
                    
                    last_size = os.path.getsize(file_path) if os.path.exists(file_path) else -1
                    time.sleep(1.5) 
                    retries -= 1
                
                self.processor.process_file(file_path)
            except Exception as e:
                print(f"❌ Error en handler auto-processor: {e}")
            finally:
                time.sleep(5) # Cooldown preventivo
                self.processing.discard(file_path)

        thread = Thread(target=wait_and_process)
        thread.daemon = True
        thread.start()
