"""
PDF Preview Service
Genera imágenes de vista previa de archivos PDF para mostrar en el modal
"""

import os
import base64
import tempfile
from typing import Dict, Optional
from pdf2image import convert_from_path


class PDFPreviewService:
    """Servicio para generar previews de PDFs como imágenes"""
    
    def __init__(self):
        self.dpi = 150  # Resolución de preview (150 DPI balance calidad/tamaño)
        self.cache_dir = tempfile.gettempdir()
    
    def generate_preview(self, pdf_path: str, page: int = 1, as_base64: bool = True) -> Dict:
        """
        Generar preview de una página del PDF
        
        Args:
            pdf_path: Ruta al archivo PDF
            page: Número de página (1-indexed)
            as_base64: Si True, retorna imagen como base64, si False retorna ruta del archivo
        
        Returns:
            {
                'success': bool,
                'image': str,  # base64 o path
                'format': str,  # 'base64' o 'file'
                'width': int,
                'height': int,
                'total_pages': int
            }
        """
        try:
            if not os.path.exists(pdf_path):
                return {'success': False, 'error': f'Archivo no encontrado: {pdf_path}'}
            
            # Convertir página a imagen
            images = convert_from_path(
                pdf_path,
                first_page=page,
                last_page=page,
                dpi=self.dpi,
                fmt='png'
            )
            
            if not images:
                return {'success': False, 'error': 'No se pudo generar imagen del PDF'}
            
            image = images[0]
            width, height = image.size
            
            # Obtener total de páginas
            from PyPDF2 import PdfReader
            try:
                pdf_reader = PdfReader(pdf_path)
                total_pages = len(pdf_reader.pages)
            except:
                total_pages = 1
            
            if as_base64:
                # Convertir a base64
                import io
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                return {
                    'success': True,
                    'image': f'data:image/png;base64,{img_base64}',
                    'format': 'base64',
                    'width': width,
                    'height': height,
                    'total_pages': total_pages
                }
            else:
                # Guardar como archivo temporal
                preview_path = os.path.join(
                    self.cache_dir,
                    f'preview_{hash(pdf_path)}_{page}.png'
                )
                image.save(preview_path, 'PNG')
                
                return {
                    'success': True,
                    'image': preview_path,
                    'format': 'file',
                    'width': width,
                    'height': height,
                    'total_pages': total_pages
                }
        
        except Exception as e:
            print(f"❌ Error generando preview PDF: {e}")
            import traceback
            traceback.print_exc()
            return {'success': False, 'error': str(e)}
    
    def generate_multi_page_preview(self, pdf_path: str, max_pages: int = 3) -> Dict:
        """
        Generar previews de múltiples páginas
        
        Args:
            pdf_path: Ruta al archivo PDF
            max_pages: Número máximo de páginas a generar (default: 3)
        
        Returns:
            {
                'success': bool,
                'pages': [
                    {'page': 1, 'image': 'base64...', 'width': 800, 'height': 1100},
                    {'page': 2, 'image': 'base64...', 'width': 800, 'height': 1100},
                    ...
                ],
                'total_pages': int
            }
        """
        try:
            if not os.path.exists(pdf_path):
                return {'success': False, 'error': f'Archivo no encontrado: {pdf_path}'}
            
            # Obtener total de páginas
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)
            
            # Limitar número de páginas
            pages_to_generate = min(max_pages, total_pages)
            
            # Convertir páginas a imágenes
            images = convert_from_path(
                pdf_path,
                first_page=1,
                last_page=pages_to_generate,
                dpi=self.dpi,
                fmt='png'
            )
            
            pages_data = []
            
            for idx, image in enumerate(images):
                width, height = image.size
                
                # Convertir a base64
                import io
                buffer = io.BytesIO()
                image.save(buffer, format='PNG')
                img_bytes = buffer.getvalue()
                img_base64 = base64.b64encode(img_bytes).decode('utf-8')
                
                pages_data.append({
                    'page': idx + 1,
                    'image': f'data:image/png;base64,{img_base64}',
                    'width': width,
                    'height': height
                })
            
            return {
                'success': True,
                'pages': pages_data,
                'total_pages': total_pages
            }
        
        except Exception as e:
            print(f"❌ Error generando preview multi-página: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_thumbnail(self, pdf_path: str, max_width: int = 200) -> Dict:
        """
        Generar thumbnail pequeña de la primera página
        """
        return self.generate_preview(pdf_path, page=1, as_base64=True)

    def generate_thumbnails(self, pdf_path: str, max_width: int = 150) -> Dict:
        """
        Generar thumbnails de todas las páginas de un PDF (v2.2.0)
        """
        try:
            if not os.path.exists(pdf_path):
                return {'success': False, 'error': f'Archivo no encontrado: {pdf_path}'}

            # Obtener número total de páginas
            from PyPDF2 import PdfReader
            pdf_reader = PdfReader(pdf_path)
            total_pages = len(pdf_reader.pages)

            # Generar thumbnails (máximo 20 para evitar overhead)
            max_thumbs = min(total_pages, 20)
            
            # Usar poppler para convertir a imágenes pequeñas
            images = convert_from_path(
                pdf_path, 
                first_page=1, 
                last_page=max_thumbs,
                dpi=72,  # Bajo DPI para thumbnails
                fmt='png'
            )

            import io
            thumbnails = []
            for i, img in enumerate(images):
                # Redimensionar si es necesario
                if img.width > max_width:
                    ratio = max_width / img.width
                    new_size = (max_width, int(img.height * ratio))
                    img = img.resize(new_size, 3) # Image.LANCZOS

                # Convertir a base64
                buffer = io.BytesIO()
                img.save(buffer, format='PNG')
                img_str = base64.b64encode(buffer.getvalue()).decode('utf-8')
                
                thumbnails.append({
                    'page': i + 1,
                    'image': f"data:image/png;base64,{img_str}"
                })

            return {
                'success': True,
                'thumbnails': thumbnails,
                'total_pages': total_pages
            }

        except Exception as e:
            print(f"❌ Error generando thumbnails: {str(e)}")
            return {'success': False, 'error': str(e)}
