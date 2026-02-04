import os
import time
import threading
from datetime import datetime

class AutoProcessorService:
    def __init__(self, ocr_service, ai_service, input_dir=None, output_dir=None):
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        self.input_dir = input_dir or os.path.expanduser("~/Desktop/PENDIENTES_LEXDOCS")
        self.output_dir = output_dir or os.path.expanduser("~/Desktop/EXPEDIENTES")
        self.running = False
        self.thread = None
        self._logs = []
        
        # Asegurar directorios
        os.makedirs(self.input_dir, exist_ok=True)
        os.makedirs(self.output_dir, exist_ok=True)

    def start(self):
        """Iniciar monitor en segundo plano"""
        if self.running:
            return {'success': True, 'message': 'Auto-Procesador ya está en ejecución'}
        
        self.running = True
        self.thread = threading.Thread(target=self._monitor_loop)
        self.thread.daemon = True
        self.thread.start()
        self._log("INFO", "Monitor iniciado correctamente")
        return {'success': True, 'message': 'Auto-Procesador iniciado'}

    def stop(self):
        """Detener monitor"""
        if not self.running:
            return {'success': True, 'message': 'Auto-Procesador ya estaba detenido'}
        
        self.running = False
        self._log("INFO", "Deteniendo monitor...")
        return {'success': True, 'message': 'Auto-Procesador detenido'}

    def get_status(self):
        """Estado actual"""
        return {
            'running': self.running,
            'input_dir': self.input_dir,
            'processed_count': len([l for l in self._logs if "Procesado" in l['message']])
        }

    def get_logs(self, limit=50):
        """Obtener últimos logs"""
        return self._logs[-limit:]

    def _monitor_loop(self):
        """Bucle principal de monitoreo"""
        self._log("INFO", f"Escaneando carpeta: {self.input_dir}")
        while self.running:
            try:
                files = [f for f in os.listdir(self.input_dir) if f.lower().endswith('.pdf')]
                for file in files:
                    if not self.running: break
                    self._process_file(file)
                
                time.sleep(5) # Escanear cada 5 segundos
            except Exception as e:
                self._log("ERROR", f"Error en ciclo de monitor: {str(e)}")
                time.sleep(10)

    def _process_file(self, filename):
        """Procesar un archivo detectado"""
        try:
            filepath = os.path.join(self.input_dir, filename)
            self._log("INFO", f"Detectado archivo: {filename}")
            
            # TODO: Aquí iría la lógica completa de clasificación con IA
            # Para Versión LITE: Mover a 'Procesados' y extraer texto básico
            
            # Simular procesamiento
            processed_dir = os.path.join(self.input_dir, "PROCESADOS")
            os.makedirs(processed_dir, exist_ok=True)
            
            new_path = os.path.join(processed_dir, filename)
            os.rename(filepath, new_path)
            
            self._log("SUCCESS", f"Procesado: {filename} -> {new_path}")
            
        except Exception as e:
            self._log("ERROR", f"Fallo al procesar {filename}: {str(e)}")

    def _log(self, level, message):
        """Registrar evento"""
        entry = {
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'level': level,
            'message': message
        }
        self._logs.append(entry)
        # Mantener logs limpios (max 1000)
        if len(self._logs) > 1000:
            self._logs.pop(0)
