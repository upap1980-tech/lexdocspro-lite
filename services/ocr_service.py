"""
Servicio de OCR mejorado para extraer texto de PDFs e imágenes
Soporta: PDF, JPG, PNG, TIFF
"""
from pathlib import Path
import os
from typing import Optional
import pytesseract
from pdf2image import convert_from_path
from PIL import Image
import pymupdf  # PyMuPDF como alternativa más rápida

class OCRService:
    def __init__(self):
        self.use_pymupdf = True  # Usar PyMuPDF por defecto (más rápido)
        self.supported_image_formats = ['.jpg', '.jpeg', '.png', '.tiff', '.tif', '.bmp']
        self.supported_pdf_formats = ['.pdf']
        
        # Verificar que tesseract esté instalado
        try:
            pytesseract.get_tesseract_version()
            print("✅ Tesseract OCR detectado")
        except Exception as e:
            print(f"⚠️ Tesseract no encontrado. Instalar con: brew install tesseract")
    
    def extraer_texto(self, file_path, page_start=None, page_end=None):
        """Método en español (alias de extract_text)"""
        return self.extract_text(file_path, page_start, page_end)
    
    def extract_text(self, file_path, page_start=None, page_end=None):
        """
        Extraer texto de PDF o imagen
        
        Args:
            file_path: Ruta al archivo (PDF o imagen)
            page_start: Página inicial (solo para PDF)
            page_end: Página final (solo para PDF)
        
        Returns:
            str: Texto extraído
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
            
            file_ext = file_path.suffix.lower()
            print(f"📄 Procesando: {file_path.name} (tipo: {file_ext})")
            
            # Determinar tipo de archivo
            if file_ext in self.supported_image_formats:
                return self._extract_from_image(file_path)
            elif file_ext in self.supported_pdf_formats:
                return self._extract_from_pdf(file_path, page_start, page_end)
            else:
                raise ValueError(f"Formato no soportado: {file_ext}. Soportados: {self.supported_image_formats + self.supported_pdf_formats}")
        
        except Exception as e:
            error_msg = f"Error al procesar {Path(file_path).name}: {str(e)}"
            print(f"❌ {error_msg}")
            raise Exception(error_msg)
    
    def _extract_from_image(self, image_path: Path) -> str:
        """
        Extraer texto de imagen usando Tesseract OCR
        """
        try:
            print(f"🖼️ Procesando imagen con OCR...")
            
            # Abrir imagen con PIL
            image = Image.open(image_path)
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Extraer texto con Tesseract
            text = pytesseract.image_to_string(image, lang='spa')
            
            if not text or len(text.strip()) < 10:
                print(f"⚠️ Poco texto extraído de la imagen ({len(text)} caracteres)")
                return text or "[No se pudo extraer texto de la imagen]"
            
            print(f"✅ Texto extraído: {len(text)} caracteres (OCR de imagen)")
            return text
        
        except Exception as e:
            raise Exception(f"Error en OCR de imagen: {str(e)}")
    
    def _extract_from_pdf(self, pdf_path: Path, page_start=None, page_end=None) -> str:
        """
        Extraer texto de PDF
        Primero intenta con PyMuPDF (rápido), si falla usa Tesseract OCR
        """
        try:
            # Método 1: PyMuPDF (rápido, para PDFs con texto nativo)
            if self.use_pymupdf:
                try:
                    doc = pymupdf.open(pdf_path)
                    text_parts = []
                    
                    # Determinar rango de páginas
                    start = page_start - 1 if page_start else 0
                    end = page_end if page_end else len(doc)
                    max_pages = min(end - start, 5)  # Limitar a 5 páginas
                    
                    for page_num in range(start, start + max_pages):
                        if page_num >= len(doc):
                            break
                        page = doc[page_num]
                        text = page.get_text()
                        text_parts.append(text)
                        print(f"  ✓ Página {page_num+1}/{len(doc)}")
                    
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
            return self._extract_from_pdf_with_ocr(pdf_path, page_start, page_end)
            
        except Exception as e:
            raise Exception(f"Error en extracción de PDF: {str(e)}")
    
    def _extract_from_pdf_with_ocr(self, pdf_path: Path, page_start=None, page_end=None) -> str:
        """
        Extraer texto de PDF escaneado usando OCR
        """
        try:
            print("🔍 Usando Tesseract OCR para PDF escaneado...")
            
            # Convertir PDF a imágenes
            start = page_start if page_start else 1
            end = page_end if page_end else start + 2  # Limitar a 3 páginas por defecto
            
            images = convert_from_path(
                pdf_path, 
                dpi=200, 
                first_page=start, 
                last_page=min(end, start + 2)
            )
            
            text_parts = []
            for i, image in enumerate(images):
                print(f"  Procesando página {start + i} con OCR...")
                text = pytesseract.image_to_string(image, lang='spa')
                text_parts.append(text)
            
            full_text = '\n\n'.join(text_parts)
            print(f"✅ Texto extraído: {len(full_text)} caracteres (OCR)")
            return full_text
        
        except Exception as e:
            raise Exception(f"Error en OCR de PDF: {str(e)}")
    
    def is_supported_file(self, filename: str) -> bool:
        """Verificar si el archivo es soportado"""
        ext = Path(filename).suffix.lower()
        return ext in (self.supported_image_formats + self.supported_pdf_formats)
    
    def get_supported_formats(self) -> list:
        """Obtener lista de formatos soportados"""
        return self.supported_image_formats + self.supported_pdf_formats
