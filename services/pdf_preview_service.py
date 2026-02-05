"""
PDF Preview Service - Generar previews de PDFs
"""
import os

class PDFPreviewService:
    def generate_preview(self, pdf_path, page=1, as_base64=True):
        """Generar preview de página de PDF"""
        try:
            import fitz  # PyMuPDF
            import base64
            from io import BytesIO
            
            doc = fitz.open(pdf_path)
            
            if page > len(doc):
                return {'success': False, 'error': 'Página fuera de rango'}
            
            page_obj = doc[page - 1]
            pix = page_obj.get_pixmap(dpi=150)
            
            img_data = pix.tobytes("png")
            
            result = {
                'success': True,
                'total_pages': len(doc),
                'width': pix.width,
                'height': pix.height
            }
            
            if as_base64:
                result['image'] = f"data:image/png;base64,{base64.b64encode(img_data).decode()}"
            else:
                result['image_bytes'] = img_data
            
            doc.close()
            return result
            
        except Exception as e:
            return {'success': False, 'error': str(e)}
    
    def generate_thumbnails(self, pdf_path):
        """Generar thumbnails de todas las páginas"""
        try:
            import fitz
            
            doc = fitz.open(pdf_path)
            thumbnails = []
            
            for i in range(min(len(doc), 10)):  # Max 10 páginas
                page = doc[i]
                pix = page.get_pixmap(dpi=72)
                thumbnails.append({
                    'page': i + 1,
                    'width': pix.width,
                    'height': pix.height
                })
            
            doc.close()
            return {'success': True, 'thumbnails': thumbnails}
            
        except Exception as e:
            return {'success': False, 'error': str(e)}

