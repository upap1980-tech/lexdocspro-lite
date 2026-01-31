"""
Servicio de exportación a iCloud Drive
"""
import os
import shutil
from pathlib import Path
from datetime import datetime

class iCloudService:
    def __init__(self):
        # Ruta base de iCloud Drive en macOS
        self.icloud_base = Path.home() / "Library/Mobile Documents/com~apple~CloudDocs"
        
        # Verificar si iCloud está disponible
        self.available = self.icloud_base.exists()
        
        if not self.available:
            print("⚠️ iCloud Drive no está disponible en este sistema")
    
    def get_expedientes_path(self):
        """Obtener ruta de carpeta EXPEDIENTES en iCloud"""
        return self.icloud_base / "EXPEDIENTES"
    
    def ensure_client_folder(self, year, client_name):
        """
        Crear estructura de carpetas para cliente si no existe
        
        Returns:
            Path: Ruta a la carpeta del cliente
        """
        if not self.available:
            raise Exception("iCloud Drive no está disponible")
        
        client_path = self.get_expedientes_path() / str(year) / client_name
        client_path.mkdir(parents=True, exist_ok=True)
        
        return client_path
    
    def export_document(self, content, filename, year=None, client_name=None, subfolder=None):
        """
        Exportar documento a iCloud
        
        Args:
            content: Contenido del documento (str)
            filename: Nombre del archivo
            year: Año (opcional, usa actual si no se especifica)
            client_name: Nombre del cliente
            subfolder: Subcarpeta adicional (ej: "LEXNET", "GENERADOS")
        
        Returns:
            str: Ruta completa del archivo guardado
        """
        if not self.available:
            raise Exception("iCloud Drive no está disponible")
        
        # Usar año actual si no se especifica
        if year is None:
            year = datetime.now().year
        
        # Construir ruta
        if client_name:
            base_path = self.ensure_client_folder(year, client_name)
        else:
            base_path = self.get_expedientes_path() / str(year)
            base_path.mkdir(parents=True, exist_ok=True)
        
        # Añadir subcarpeta si se especifica
        if subfolder:
            base_path = base_path / subfolder
            base_path.mkdir(parents=True, exist_ok=True)
        
        # Guardar archivo
        filepath = base_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        print(f"✅ Exportado a iCloud: {filepath}")
        
        return str(filepath)
    
    def export_analysis_to_client(self, analysis_content, client_name):
        """
        Exportar análisis LexNET directamente a carpeta del cliente
        
        Args:
            analysis_content: Contenido del análisis
            client_name: Nombre del cliente
        
        Returns:
            str: Ruta del archivo exportado
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"ANALISIS_LEXNET_{timestamp}.txt"
        
        return self.export_document(
            content=analysis_content,
            filename=filename,
            year=datetime.now().year,
            client_name=client_name,
            subfolder="LEXNET"
        )
    
    def list_clients(self, year=None):
        """
        Listar clientes en iCloud
        
        Args:
            year: Año específico (None para año actual)
        
        Returns:
            list: Lista de nombres de clientes
        """
        if not self.available:
            return []
        
        if year is None:
            year = datetime.now().year
        
        year_path = self.get_expedientes_path() / str(year)
        
        if not year_path.exists():
            return []
        
        clients = [d.name for d in year_path.iterdir() if d.is_dir()]
        return sorted(clients)
    
    def get_icloud_status(self):
        """Obtener estado de iCloud"""
        return {
            'available': self.available,
            'path': str(self.icloud_base) if self.available else None,
            'expedientes_exists': (self.get_expedientes_path().exists() if self.available else False)
        }
