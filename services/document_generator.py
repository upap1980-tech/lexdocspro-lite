"""
Generador de documentos jurídicos profesionales
"""
from jinja2 import Template
from datetime import datetime
from pathlib import Path
import json

class DocumentGenerator:
    """Generador de documentos legales"""
    
    def __init__(self, ai_service):
        self.ai_service = ai_service
        self.templates_dir = Path(__file__).parent / 'templates' / 'legal'
        
    def generate_document(self, doc_type: str, data: dict, 
                         provider: str = 'ollama') -> str:
        """
        Generar documento jurídico profesional
        
        Args:
            doc_type: demanda, recurso, contrato, escrito, burofax
            data: Datos del documento
            provider: Proveedor de IA a usar
        """
        
        # Prompt especializado por tipo de documento
        prompts = {
            'demanda': self._prompt_demanda,
            'recurso': self._prompt_recurso,
            'contrato': self._prompt_contrato,
            'escrito': self._prompt_escrito,
            'burofax': self._prompt_burofax
        }
        
        if doc_type not in prompts:
            return "Tipo de documento no soportado"
        
        # Generar con IA
        prompt = prompts[doc_type](data)
        result = self.ai_service.chat(
            prompt=prompt,
            provider=provider,
            mode='deep'
        )
        
        if not result['success']:
            return f"Error: {result.get('error')}"
        
        # Post-procesar documento
        document = self._format_legal_document(result['response'], doc_type, data)
        
        return document
    
    def _prompt_demanda(self, data: dict) -> str:
        return f"""Genera una DEMANDA JUDICIAL profesional para el derecho español con los siguientes datos:

TIPO DE PROCEDIMIENTO: {data.get('tipo_procedimiento', 'Ordinario')}
JUZGADO: {data.get('juzgado', 'Juzgado de Primera Instancia')}
MATERIA: {data.get('materia', '')}

DATOS DEL DEMANDANTE:
{data.get('demandante', '')}

DATOS DEL DEMANDADO:
{data.get('demandado', '')}

HECHOS:
{data.get('hechos', '')}

PETICIONES:
{data.get('peticiones', '')}

DOCUMENTACIÓN ADJUNTA:
{data.get('documentos', '')}

GENERA UNA DEMANDA COMPLETA Y PROFESIONAL que incluya:
1. Encabezamiento con identificación de partes y juzgado
2. Sección de HECHOS numerados y detallados
3. Sección de FUNDAMENTOS DE DERECHO con cita de artículos
4. PETITUM con las solicitudes concretas
5. OTROSÍ DIGO con solicitud de documentación si procede
6. Cierre formal con fecha y firma

Usa lenguaje jurídico técnico profesional español."""

    def _prompt_recurso(self, data: dict) -> str:
        return f"""Genera un RECURSO profesional para el derecho español:

TIPO DE RECURSO: {data.get('tipo_recurso', 'Apelación')}
RESOLUCIÓN RECURRIDA: {data.get('resolucion', '')}
TRIBUNAL: {data.get('tribunal', '')}

PARTE RECURRENTE:
{data.get('recurrente', '')}

PARTE RECURRIDA:
{data.get('recurrido', '')}

MOTIVOS DE RECURSO:
{data.get('motivos', '')}

PRETENSIÓN:
{data.get('pretension', '')}

GENERA UN RECURSO COMPLETO que incluya:
1. Encabezamiento y comparecencia
2. ANTECEDENTES procesales
3. MOTIVOS DEL RECURSO numerados con fundamentación jurídica
4. Cita de jurisprudencia relevante del Tribunal Supremo
5. SUPLICO con las peticiones
6. Cierre formal

Lenguaje técnico procesal español."""

    def _prompt_contrato(self, data: dict) -> str:
        return f"""Redacta un CONTRATO profesional según derecho español:

TIPO DE CONTRATO: {data.get('tipo_contrato', '')}

PARTE CONTRATANTE 1:
{data.get('parte1', '')}

PARTE CONTRATANTE 2:
{data.get('parte2', '')}

OBJETO DEL CONTRATO:
{data.get('objeto', '')}

CONDICIONES ESPECÍFICAS:
{data.get('condiciones', '')}

PLAZO Y PRECIO:
{data.get('plazo_precio', '')}

GENERA UN CONTRATO COMPLETO que incluya:
1. Encabezamiento y comparecencia de partes
2. EXPONEN (antecedentes y capacidades)
3. CLÁUSULAS numeradas:
   - Objeto del contrato
   - Obligaciones de las partes
   - Precio y forma de pago
   - Plazo y vigencia
   - Responsabilidades
   - Resolución y causas
   - Confidencialidad (si procede)
   - Jurisdicción y ley aplicable
4. Cierre con firma de partes

Redacción clara, técnica y equilibrada según Código Civil español."""

    def _prompt_escrito(self, data: dict) -> str:
        return f"""Redacta un ESCRITO PROCESAL profesional:

TIPO: {data.get('tipo_escrito', 'Escrito de alegaciones')}
DESTINATARIO: {data.get('destinatario', '')}
PROCEDIMIENTO: {data.get('procedimiento', '')}

PARTE SOLICITANTE:
{data.get('solicitante', '')}

SOLICITUD:
{data.get('solicitud', '')}

FUNDAMENTACIÓN:
{data.get('fundamentacion', '')}

GENERA UN ESCRITO COMPLETO con:
1. Encabezamiento y comparecencia
2. EXPONE (hechos y situación procesal)
3. Fundamentación jurídica con citas legales
4. SOLICITA/SUPLICA
5. Cierre formal

Lenguaje procesal técnico español."""

    def _prompt_burofax(self, data: dict) -> str:
        return f"""Redacta un BUROFAX profesional:

REMITENTE:
{data.get('remitente', '')}

DESTINATARIO:
{data.get('destinatario', '')}

ASUNTO:
{data.get('asunto', '')}

CONTENIDO:
{data.get('contenido', '')}

REQUERIMIENTO:
{data.get('requerimiento', '')}

GENERA UN BUROFAX que incluya:
1. Datos de remitente y destinatario
2. Exposición de hechos clara y concisa
3. Fundamentación legal si procede
4. Requerimiento concreto
5. Advertencia de consecuencias legales
6. Plazo para respuesta

Tono firme pero profesional."""

    def _format_legal_document(self, content: str, doc_type: str, data: dict) -> str:
        """Formatear documento con encabezado y pie"""
        
        header = f"""
{'='*80}
DOCUMENTO GENERADO POR LEXDOCSPRO LITE v2.0
Tipo: {doc_type.upper()}
Fecha: {datetime.now().strftime('%d de %B de %Y')}
{'='*80}

"""
        
        footer = f"""

{'='*80}
NOTA: Este documento ha sido generado automáticamente y debe ser revisado
por un abogado colegiado antes de su presentación o uso oficial.
{'='*80}
"""
        
        return header + content + footer
