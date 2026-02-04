import os
from datetime import datetime

class LexNetNotifications:
    def __init__(self, base_dir=None):
        self.base_dir = base_dir or os.path.expanduser("~/Desktop/PENDIENTES_LEXNET")
        os.makedirs(self.base_dir, exist_ok=True)

    def get_notifications(self, filter_read=False):
        """Listar archivos en carpeta LexNET simulando notificaciones"""
        notifications = []
        if not os.path.exists(self.base_dir):
            return []
            
        files = [f for f in os.listdir(self.base_dir) if f.lower().endswith('.pdf')]
        
        for idx, f in enumerate(files):
            # Simulamos metadatos basados en nombre de archivo
            notifications.append({
                'id': idx + 1,
                'asunto': f,
                'fecha': datetime.fromtimestamp(os.path.getmtime(os.path.join(self.base_dir, f))).strftime('%d/%m/%Y %H:%M'),
                'remitente': 'Juzgado Simulado',
                'leido': False,
                'prioridad': 'NORMAL',
                'filepath': os.path.join(self.base_dir, f)
            })
            
        return notifications

    def mark_as_read(self, notification_id):
        # En versión file-system, esto podría mover el archivo a "LEIDOS"
        return {'success': True, 'message': 'Marcado como leído'}
