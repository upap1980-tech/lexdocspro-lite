import os
from pathlib import Path


class OCRService:
    def __init__(self):
        self.supported_extensions = {".pdf", ".png", ".jpg", ".jpeg", ".tiff", ".tif"}

    def get_supported_formats(self):
        return sorted(self.supported_extensions)

    def is_supported_file(self, filename):
        if not filename:
            return False
        return Path(filename).suffix.lower() in self.supported_extensions

    def extract_text(self, filepath):
        """OCR Privacy-First: Tesseract local"""
        try:
            import pytesseract
            from pdf2image import convert_from_path
            from PIL import Image

            pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

            if filepath.lower().endswith('.pdf'):
                images = convert_from_path(filepath, dpi=200)
                text = '\n'.join(pytesseract.image_to_string(img, lang='spa') for img in images[:3])
            else:
                img = Image.open(filepath)
                text = pytesseract.image_to_string(img, lang='spa')
            return text.strip() or "Texto no detectado"
        except Exception as e:
            return f"OCR Error: {str(e)}"

    def extraer_texto(self, filepath):
        """
        Compatibilidad con llamadas legacy.
        Retorna texto plano para no romper rutas existentes.
        """
        return self.extract_text(filepath)
