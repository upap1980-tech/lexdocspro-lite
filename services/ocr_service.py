"""
Servicio de OCR para extraer texto de PDFs e imágenes
"""
from pathlib import Path
import pytesseract
from pdf2image import convert_from_path
import pymupdf  # PyMuPDF como alternativa más rápida

class OCRService:
    def __init__(self):
        self.use_pymupdf = True  # Usar PyMuPDF por defecto (más rápido)
    
    def extraer_texto(self, pdf_path):
        """Método en español (alias de extract_text)"""
        return self.extract_text(pdf_path)
    
    def extract_text(self, pdf_path):
        """
        Extraer texto de PDF
        Primero intenta con PyMuPDF (rápido), si falla usa Tesseract OCR
        """
        try:
            print(f"📄 Procesando: {Path(pdf_path).name}")
            
            # Método 1: PyMuPDF (rápido, para PDFs con texto)
            if self.use_pymupdf:
                try:
                    doc = pymupdf.open(pdf_path)
                    text_parts = []
                    
                    # Limitar a primeras 5 páginas para velocidad
                    max_pages = min(len(doc), 5)
                    
                    for page_num in range(max_pages):
                        page = doc[page_num]
                        text = page.get_text()
                        text_parts.append(text)
                        print(f"  ✓ Página {page_num+1}/{max_pages}")
                    
                    doc.close()
                    
                    full_text = '\n\n'.join(text_parts)
                    
                    # Si tiene suficiente texto, retornar
                    if len(full_text.strip()) > 100:
                        print(f"✅ Texto extraído: {len(full_text)} caracteres (PyMuPDF)")
                        return full_text
                    else:
                        print("⚠️ Poco texto con PyMuPDF, intentando OCR...")
                
                except Exception as e:
                    print(f"⚠️ PyMuPDF falló: {e}, intentando OCR...")
            
            # Método 2: Tesseract OCR (lento, para PDFs escaneados)
            print("🔍 Usando Tesseract OCR...")
            images = convert_from_path(pdf_path, dpi=200, first_page=1, last_page=3)
            
            text_parts = []
            for i, image in enumerate(images):
                print(f"  Procesando página {i+1}/{len(images)} con OCR...")
                text = pytesseract.image_to_string(image, lang='spa')
                text_parts.append(text)
            
            full_text = '\n\n'.join(text_parts)
            print(f"✅ Texto extraído: {len(full_text)} caracteres (OCR)")
            return full_text
            
        except Exception as e:
            error_msg = f"Error al procesar {Path(pdf_path).name}: {str(e)}"
            print(f"❌ {error_msg}")
            return f"[ERROR: {error_msg}]"
