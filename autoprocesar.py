#!/usr/bin/env python3
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from config import PENDIENTES_DIR, AUTOPROCESAR_LOG
import requests
import logging
from datetime import datetime

logging.basicConfig(filename=str(AUTOPROCESAR_LOG), level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

class LexDocsHandler(FileSystemEventHandler):
    def on_created(self, event):
        if not event.is_directory and event.src_path.endswith(('.pdf', '.jpg', '.png')):
            logging.info(f"Nuevo archivo detectado: {event.src_path}")
            try:
                with open(event.src_path, 'rb') as f:
                    files = {'file': f}
                    response = requests.post('http://localhost:5001/api/lexnet-analyze', files=files)
                if response.status_code == 200:
                    logging.info("✅ Procesado OK")
                else:
                    logging.error(f"❌ Error: {response.text}")
            except Exception as e:
                logging.error(f"❌ Error procesando: {e}")

if __name__ == "__main__":
    print(f"🔄 Monitorizando: {PENDIENTES_DIR}")
    print(f"📝 Logs: {AUTOPROCESAR_LOG}")
    event_handler = LexDocsHandler()
    observer = Observer()
    observer.schedule(event_handler, str(PENDIENTES_DIR), recursive=False)
    observer.start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
