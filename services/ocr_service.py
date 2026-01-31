from pathlib import Path
import pytesseract
from pdf2image import convert_from_path

class OCRService:
    def extract_text(self, pdf_path):
        try:
            images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=3)
            
            text_parts = []
            for i, image in enumerate(images):
                print(f"  Procesando página {i+1}/{len(images)}...")
                text = pytesseract.image_to_string(image, lang='spa')
                text_parts.append(text)
            
            return '\n\n'.join(text_parts)
            
        except Exception as e:
            print(f"❌ Error en OCR: {e}")
            return f"Error: {str(e)}"
