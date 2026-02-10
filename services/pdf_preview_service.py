"""
PDF Preview Service - Generar previews de PDFs
"""
import os
import base64

class PDFPreviewService:
    def generate_preview(self, pdf_path, page=1, as_base64=True):
        """Generar preview de página de PDF"""
        try:
            import fitz  # PyMuPDF
            
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
            # Fallback sin PyMuPDF: devolver placeholder y total de páginas.
            total_pages = 1
            try:
                try:
                    from pypdf import PdfReader
                except Exception:
                    from PyPDF2 import PdfReader
                total_pages = len(PdfReader(pdf_path).pages) or 1
            except Exception:
                pass

            svg = (
                "<svg xmlns='http://www.w3.org/2000/svg' width='900' height='1200'>"
                "<rect width='100%' height='100%' fill='#f1f5f9'/>"
                "<text x='50%' y='45%' dominant-baseline='middle' text-anchor='middle' "
                "font-family='Arial' font-size='26' fill='#0f172a'>Preview no disponible</text>"
                "<text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' "
                "font-family='Arial' font-size='18' fill='#334155'>PyMuPDF no operativo en entorno</text>"
                f"<text x='50%' y='55%' dominant-baseline='middle' text-anchor='middle' "
                f"font-family='Arial' font-size='14' fill='#475569'>Detalle: {str(e)[:140]}</text>"
                "</svg>"
            )
            data_uri = "data:image/svg+xml;base64," + base64.b64encode(svg.encode("utf-8")).decode("ascii")
            return {
                'success': True,
                'fallback': True,
                'total_pages': total_pages,
                'width': 900,
                'height': 1200,
                'image': data_uri,
                'warning': f'Fallback activo: {e}'
            }
    
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
            # Fallback sin PyMuPDF: devolver miniatura estructural por número de página.
            try:
                try:
                    from pypdf import PdfReader
                except Exception:
                    from PyPDF2 import PdfReader
                total = len(PdfReader(pdf_path).pages)
            except Exception:
                total = 1

            thumbnails = []
            for i in range(min(total, 10)):
                thumbnails.append({
                    'page': i + 1,
                    'width': 120,
                    'height': 170,
                    'fallback': True
                })
            return {'success': True, 'thumbnails': thumbnails, 'warning': f'Fallback activo: {e}'}
