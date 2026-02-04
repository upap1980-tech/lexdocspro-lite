"""
Document Processing Service - Procesamiento inteligente de documentos legales
Extracción mejorada con IA, propuesta de clasificación, y guardado con confirmación
"""
import os
import json
import re
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, List, Tuple
from services.ocr_service import OCRService
from services.ai_service import AIService

class DocumentProcessingService:
    """Servicio para procesamiento inteligente de documentos con confirmación humana"""
    
    def __init__(self, ocr_service: OCRService, ai_service: AIService, base_dir: str):
        self.ocr_service = ocr_service
        self.ai_service = ai_service
        self.base_dir = Path(base_dir)
        self.current_year = datetime.now().year
        
        # Tipos de documentos predefinidos
        self.document_types = [
            "Demanda Civil",
            "Demanda Laboral",
            "Demanda Penal",
            "Recurso de Apelación",
            "Recurso de Casación",
            "Escrito de Oposición",
            "Escrito de Acusación (MF)",
            "Escrito de Defensa",
            "Notificación LexNET",
            "Auto Judicial",
            "Sentencia",
            "Providencia",
            "Decreto",
            "Contrato",
            "Poder Notarial",
            "Demanda Laboral",
            "Querella",
            "Denuncia",
            "Otro"
        ]
    
    def get_document_types(self) -> List[str]:
        """Obtener lista de tipos de documentos soportados"""
        return self.document_types
    
    def extract_metadata(self, file_path: str, hint_year: Optional[int] = None) -> Dict:
        """
        Extraer metadata completa del documento usando IA
        
        Args:
            file_path: Ruta al archivo (PDF o imagen)
            hint_year: Año sugerido (opcional)
        
        Returns:
            Dict con metadata extraída
        """
        try:
            # 1. Extraer texto con OCR
            print(f"🔍 Extrayendo texto de {Path(file_path).name}...")
            text = self.ocr_service.extract_text(file_path)
            
            if not text or len(text) < 50:
                return {
                    'success': False,
                    'error': 'No se pudo extraer suficiente texto del documento'
                }
            
            # 2. Analizar con IA
            print(f"🤖 Analizando documento con IA...")
            metadata = self._analyze_with_ai(text[:5000], hint_year)
            
            # 3. Validar y enriquecer
            metadata = self._validate_and_enrich_metadata(metadata, hint_year)
            
            return {
                'success': True,
                'metadata': metadata,
                'text_preview': text[:500]
            }
        
        except Exception as e:
            print(f"❌ Error extrayendo metadata: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _analyze_with_ai(self, text: str, hint_year: Optional[int] = None) -> Dict:
        """Analizar texto con IA para extraer metadata estructurada"""
        
        prompt_sistema = """Eres un experto en análisis de documentos legales españoles.
Tu tarea es extraer información estructurada con máxima precisión.
Responde SOLO con JSON válido, sin markdown ni explicaciones."""

        current_year = hint_year or self.current_year
        
        prompt_usuario = f"""Analiza este documento legal español y extrae la siguiente información:

DOCUMENTO:
{text}

INSTRUCCIONES CRÍTICAS:

1. **CLIENTE/PARTE** (NO abogado):
   - Los abogados tienen número colegiado [XXX] → EXCLUIR
   - Buscar en secciones: DEMANDANTE, DEMANDADO, IMPUTADO, ASEGURADO, PARTE
   - Si formato "APELLIDOS, NOMBRE" → convertir a "Nombre Apellidos"
   - Ejemplo válido: "María Pérez García"
   - Ejemplo inválido: "Victor Manuel Francisco Herrera [593]" (es abogado)

2. **TIPO DE DOCUMENTO** (clasificación exacta):
   - "Demanda Civil", "Demanda Penal", "Escrito de Acusación (MF)"
   - "Recurso de Apelación", "Escrito de Oposición"
   - "Notificación LexNET", "Auto Judicial", "Sentencia"
   - Si no encaja en predefinidos → describir brevemente

3. **AÑO DEL ASUNTO** (importante):
   - NO confundir con fechas internas del documento
   - Si el documento es del año {current_year} → año = {current_year}
   - Si es notificación o trámite reciente → año = {current_year}
   - Solo usar año antiguo si claramente es un caso histórico

4. **FECHA DEL DOCUMENTO**: Formato DD/MM/YYYY

5. **NÚMERO DE EXPEDIENTE**: NIG, autos, procedimiento (ej: "123/2022", "NIG: 28079...")

6. **JUZGADO**: Nombre completo si aparece

7. **IMPORTE TOTAL**: Si es una factura o demanda económica, extraer importe numérico (ej: 3500.50).
8. **CONFIANZA**: Nivel de certeza (60-100%)

Responde EXACTAMENTE con este JSON (sin ```json):
{{
  "cliente": "Nombre completo del cliente",
  "tipo_documento": "Tipo exacto",
  "fecha_documento": "DD/MM/YYYY",
  "ano_asunto": {current_year},
  "numero_expediente": "XXX/YYYY o null",
  "juzgado": "Nombre juzgado o null",
  "importe_total": 0.0,
  "confianza": 85
}}"""

        try:
            # Usar sistema de cascada (v2.3.0)
            result = self.ai_service.chat_cascade(
                prompt=prompt_usuario,
                context=prompt_sistema,
                mode='standard'
            )
            
            if not result.get('success'):
                print(f"⚠️ Cascada de IA falló: {result.get('error')}, usando fallback regex")
                return self._extract_metadata_fallback(text)
                
            response = result.get('response', '')
            
            # Extraer JSON de la respuesta
            json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response, re.DOTALL)
            
            if json_match:
                metadata = json.loads(json_match.group())
                print(f"✅ Metadata extraída por IA ({result.get('provider')}): {metadata}")
                return metadata
            else:
                print(f"⚠️ No se encontró JSON en respuesta de {result.get('provider')}, usando fallback")
                raise ValueError("No JSON en respuesta")
        
        except Exception as e:
            print(f"⚠️ Error con IA: {e}, usando valores por defecto")
            # Fallback: extracción básica con regex
            return self._extract_metadata_fallback(text)
    
    def _extract_metadata_fallback(self, text: str) -> Dict:
        """Extracción básica con regex como fallback"""
        metadata = {
            "cliente": "SIN_CLASIFICAR",
            "tipo_documento": "Documento",
            "fecha_documento": datetime.now().strftime("%d/%m/%Y"),
            "ano_asunto": self.current_year,
            "numero_expediente": None,
            "juzgado": None,
            "confianza": 50
        }
        
        # Intentar extraer fecha con regex
        fecha_match = re.search(r'(\d{1,2})[/-](\d{1,2})[/-](\d{4})', text)
        if fecha_match:
            day, month, year = fecha_match.groups()
            metadata['fecha_documento'] = f"{day.zfill(2)}/{month.zfill(2)}/{year}"
        
        # Intentar extraer expediente
        exp_match = re.search(r'(?:expediente|autos|procedimiento)[:\s]*([0-9/]+)', text, re.IGNORECASE)
        if exp_match:
            metadata['numero_expediente'] = exp_match.group(1)
        
        return metadata
    
    def _validate_and_enrich_metadata(self, metadata: Dict, hint_year: Optional[int] = None) -> Dict:
        """Validar y enriquecer metadata extraída"""
        
        # Asegurar año correcto
        if hint_year:
            metadata['ano_asunto'] = hint_year
        elif not metadata.get('ano_asunto') or metadata['ano_asunto'] < 2020:
            metadata['ano_asunto'] = self.current_year
        
        # Normalizar cliente
        cliente = metadata.get('cliente', 'SIN_CLASIFICAR')
        metadata['cliente'] = self._normalize_client_name(cliente)
        
        # Normalizar fecha
        if metadata.get('fecha_documento'):
            try:
                # Convertir a formato estándar
                parts = metadata['fecha_documento'].split('/')
                if len(parts) == 3:
                    metadata['fecha_documento'] = f"{parts[0].zfill(2)}/{parts[1].zfill(2)}/{parts[2]}"
            except:
                metadata['fecha_documento'] = datetime.now().strftime("%d/%m/%Y")
        
        return metadata
    
    def _normalize_client_name(self, name: str) -> str:
        """Normalizar nombre de cliente"""
        if not name or name == "SIN_CLASIFICAR":
            return "SIN_CLASIFICAR"
        
        # Remover caracteres especiales
        name = re.sub(r'[^\w\s-]', '', name).strip()
        
        # Si está en formato "APELLIDOS, NOMBRE" → "Nombre Apellidos"
        if ',' in name:
            parts = name.split(',')
            name = f"{parts[1].strip()} {parts[0].strip()}"
        
        # Capitalizar correctamente
        name = ' '.join(word.capitalize() for word in name.split())
        
        return name
    
    def propose_save(self, temp_file_path: str, metadata: Dict) -> Dict:
        """
        Proponer clasificación y ruta de guardado
        
        Args:
            temp_file_path: Ruta temporal del archivo
            metadata: Metadata extraída del documento
        
        Returns:
            Dict con propuesta de guardado
        """
        try:
            cliente = metadata.get('cliente', 'SIN_CLASIFICAR')
            ano = metadata.get('ano_asunto', self.current_year)
            tipo = metadata.get('tipo_documento', 'Documento')
            fecha = metadata.get('fecha_documento', datetime.now().strftime("%d/%m/%Y"))
            
            # Buscar cliente existente
            existing_client = self._find_existing_client(cliente, ano)
            
            # Generar opciones de ruta
            path_options = self._generate_path_options(cliente, ano, existing_client)
            
            # Ruta sugerida (primera opción)
            suggested_path = path_options[0]['path'] if path_options else None
            
            # Nombre de archivo sugerido
            fecha_parts = fecha.split('/')
            fecha_filename = f"{ano}-{fecha_parts[1]}-{fecha_parts[0]}" if len(fecha_parts) == 3 else f"{ano}-XX-XX"
            tipo_slug = self._slugify(tipo)
            suggested_filename = f"{fecha_filename}_{tipo_slug}.pdf"
            
            return {
                'success': True,
                'proposal': {
                    'client': cliente,
                    'doc_type': tipo,
                    'date': fecha,
                    'expedient': metadata.get('numero_expediente'),
                    'court': metadata.get('juzgado'),
                    'confidence': metadata.get('confianza', 70),
                    'suggested_year': ano,
                    'suggested_path': suggested_path,
                    'suggested_filename': suggested_filename,
                    'path_options': path_options
                },
                'existing_client': existing_client
            }
        
        except Exception as e:
            print(f"❌ Error proponiendo guardado: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _find_existing_client(self, client_name: str, year: int) -> Optional[Dict]:
        """Buscar carpeta de cliente existente"""
        year_folder = self.base_dir / str(year)
        
        if not year_folder.exists():
            return None
        
        client_slug = self._slugify(client_name)
        
        for folder in year_folder.iterdir():
            if folder.is_dir() and client_slug.lower() in folder.name.lower():
                # Contar documentos
                doc_count = len(list(folder.glob('*.pdf')))
                
                return {
                    'found': True,
                    'folder': folder.name,
                    'full_path': str(folder),
                    'document_count': doc_count
                }
        
        return None
    
    def _generate_path_options(self, client_name: str, year: int, existing_client: Optional[Dict]) -> List[Dict]:
        """Generar opciones de rutas para guardar"""
        options = []
        
        # Opción 1: Cliente existente (si hay)
        if existing_client:
            options.append({
                'path': existing_client['full_path'],
                'display': f"{year}/{existing_client['folder']}",
                'client': client_name,
                'document_count': existing_client['document_count'],
                'is_new': False
            })
        
       # Opción 2: Nueva carpeta para el cliente
        year_folder = self.base_dir / str(year)
        client_slug = self._slugify(client_name)
        
        # Determinar código siguiente
        next_code = self._get_next_client_code(year)
        new_folder_name = f"{year}-{next_code:02d}_{client_slug}"
        new_folder_path = year_folder / new_folder_name
        
        options.append({
            'path': str(new_folder_path),
            'display': f"{year}/{new_folder_name}",
            'client': client_name,
            'document_count': 0,
            'is_new': True
        })
        
        return options
    
    def _get_next_client_code(self, year: int) -> int:
        """Obtener siguiente código de cliente para el año"""
        year_folder = self.base_dir / str(year)
        
        if not year_folder.exists():
            return 1
        
        codes = []
        for folder in year_folder.iterdir():
            if folder.is_dir():
                match = re.match(r'(\d{4})-(\d{2})', folder.name)
                if match:
                    codes.append(int(match.group(2)))
        
        return max(codes, default=0) + 1
    
    def _slugify(self, text: str) -> str:
        """Convertir texto a slug seguro para nombres de archivo/carpeta"""
        # Remover acentos y caracteres especiales
        text = text.replace('á', 'a').replace('é', 'e').replace('í', 'i')
        text = text.replace('ó', 'o').replace('ú', 'u').replace('ñ', 'n')
        text = text.replace('Á', 'A').replace('É', 'E').replace('Í', 'I')
        text = text.replace('Ó', 'O').replace('Ú', 'U').replace('Ñ', 'N')
        
        # Remover caracteres no alfanuméricos (excepto espacios y guiones)
        text = re.sub(r'[^\w\s-]', '', text)
        
        # Reemplazar espacios por guiones bajos
        text = re.sub(r'[-\s]+', '_', text)
        
        # Limitar longitud
        return text[:50].strip('_')
    
    def confirm_save(self, temp_file_path: str, confirmed_data: Dict, user_id: Optional[int] = None) -> Dict:
        """
        Guardar documento con datos confirmados por el usuario
        
        Args:
            temp_file_path: Ruta temporal del archivo
            confirmed_data: Datos confirmados por el usuario
            user_id: ID del usuario que confirma (opcional)
        
        Returns:
            Dict con resultado del guardado
        """
        try:
            temp_file = Path(temp_file_path)
            
            if not temp_file.exists():
                return {
                    'success': False,
                    'error': f'Archivo temporal no encontrado: {temp_file_path}'
                }
            
            # Parsear datos confirmados
            dest_path = Path(confirmed_data['path'])
            filename = confirmed_data['filename']
            
            # Crear carpeta si no existe
            dest_path.mkdir(parents=True, exist_ok=True)
            
            # Ruta final del archivo
            final_file_path = dest_path / filename
            
            # Si ya existe, añadir timestamp
            if final_file_path.exists():
                timestamp = datetime.now().strftime("%H%M%S")
                name_parts = filename.rsplit('.', 1)
                filename = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                final_file_path = dest_path / filename
            
            # Mover archivo con retry
            success = self._move_file_with_retry(temp_file, final_file_path)
            
            if not success:
                return {
                    'success': False,
                    'error': 'Error al mover el archivo después de 3 intentos'
                }
            
            print(f"✅ Documento guardado: {final_file_path}")
            
            return {
                'success': True,
                'message': 'Documento guardado correctamente',
                'final_path': str(final_file_path),
                'document_data': confirmed_data
            }
        
        except Exception as e:
            print(f"❌ Error guardando documento: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _move_file_with_retry(self, src: Path, dest: Path, max_retries: int = 3) -> bool:
        """Mover archivo con reintentos"""
        import time
        
        for attempt in range(max_retries):
            try:
                shutil.move(str(src), str(dest))
                return True
            except Exception as e:
                print(f"⚠️ Intento {attempt + 1}/{max_retries} falló: {e}")
                if attempt < max_retries - 1:
                    time.sleep(0.5 * (attempt + 1))  # Backoff exponencial
                else:
                    print(f"❌ Error después de {max_retries} intentos")
                    return False
        
        return False
    
    def get_path_options(self, year: int, client_filter: Optional[str] = None) -> List[Dict]:
        """Obtener opciones de carpetas existentes para un año"""
        year_folder = self.base_dir / str(year)
        
        if not year_folder.exists():
            return []
        
        options = []
        
        for folder in sorted(year_folder.iterdir()):
            if not folder.is_dir():
                continue
            
            # Filtrar por cliente si se especifica
            if client_filter and client_filter.lower() not in folder.name.lower():
                continue
            
            # Extraer nombre de cliente del nombre de carpeta
            match = re.match(r'\d{4}-\d{2}_(.+)', folder.name)
            client_name = match.group(1).replace('_', ' ') if match else folder.name
            
            # Contar documentos
            doc_count = len(list(folder.glob('*.pdf')))
            
            # Última modificación
            last_modified = datetime.fromtimestamp(folder.stat().st_mtime)
            
            options.append({
                'path': str(folder),
                'display': f"{year}/{folder.name}",
                'client': client_name,
                'document_count': doc_count,
                'last_modified': last_modified.isoformat(),
                'is_new': False
            })
        
        return options
