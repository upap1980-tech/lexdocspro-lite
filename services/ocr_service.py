import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import os

pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

class OCRService:
    def __init__(self):
        pass

    def extract_text(self, filepath):
        """OCR Privacy-First: Tesseract local"""
        try:
            if filepath.lower().endswith('.pdf'):
                images = convert_from_path(filepath, dpi=200)
                text = '\n'.join(pytesseract.image_to_string(img, lang='spa') for img in images[:3])
            else:
                img = Image.open(filepath)
                text = pytesseract.image_to_string(img, lang='spa')
            return text.strip() or "Texto no detectado"
        except Exception as e:
            return f"OCR Error: {str(e)}"
