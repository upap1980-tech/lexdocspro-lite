"""
Generador de documentos legales con IA
Versión completa y sin errores
"""
from datetime import datetime
import os


class DocumentGenerator:
    def __init__(self, ai_service, ai_agent_service=None):
        self.ai_service = ai_service
        self.ai_agent = ai_agent_service
    
    def get_templates(self):
        """Retorna todos los templates disponibles"""
        return {
            'demanda_civil': {
                'name': '⚖️ Demanda Civil',
                'description': 'Demanda completa para juicio ordinario o verbal',
                'fields': [
                    {'name': 'juzgado', 'label': 'Juzgado', 'type': 'text'},
                    {'name': 'demandante', 'label': 'Demandante', 'type': 'text'},
                    {'name': 'demandado', 'label': 'Demandado', 'type': 'text'},
                    {'name': 'hechos', 'label': 'Hechos', 'type': 'textarea'},
                    {'name': 'petitorio', 'label': 'Petitorio', 'type': 'textarea'}
                ]
            },
            'contestacion_demanda': {
                'name': '🛡️ Contestación a la Demanda',
                'description': 'Respuesta formal a demanda civil',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'demandado', 'label': 'Demandado (quien contesta)', 'type': 'text'},
                    {'name': 'hechos_propios', 'label': 'Hechos propios', 'type': 'textarea'},
                    {'name': 'excepciones', 'label': 'Excepciones y defensas', 'type': 'textarea'},
                    {'name': 'suplica', 'label': 'Súplica', 'type': 'textarea'}
                ]
            },
            'recurso_apelacion': {
                'name': '🔄 Recurso de Apelación',
                'description': 'Recurso contra sentencia de primera instancia',
                'fields': [
                    {'name': 'sentencia', 'label': 'Sentencia a recurrir', 'type': 'text'},
                    {'name': 'recurrente', 'label': 'Recurrente', 'type': 'text'},
                    {'name': 'fundamentos', 'label': 'Fundamentos de Derecho', 'type': 'textarea'},
                    {'name': 'suplica', 'label': 'Súplica', 'type': 'textarea'}
                ]
            },
            'recurso_reposicion': {
                'name': '🔁 Recurso de Reposición',
                'description': 'Recurso contra autos y providencias',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'resolucion', 'label': 'Resolución recurrida', 'type': 'text'},
                    {'name': 'recurrente', 'label': 'Recurrente', 'type': 'text'},
                    {'name': 'motivos', 'label': 'Motivos del recurso', 'type': 'textarea'}
                ]
            },
            'escrito_alegaciones': {
                'name': '📝 Escrito de Alegaciones',
                'description': 'Respuesta a trámite de alegaciones',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'En nombre de', 'type': 'text'},
                    {'name': 'alegaciones', 'label': 'Alegaciones', 'type': 'textarea'}
                ]
            },
            'desistimiento': {
                'name': '🚫 Desistimiento',
                'description': 'Escrito de desistimiento del procedimiento',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'Parte que desiste', 'type': 'text'},
                    {'name': 'motivo', 'label': 'Motivo (opcional)', 'type': 'textarea'}
                ]
            },
            'personacion': {
                'name': '👤 Personación y Solicitud de Copias',
                'description': 'Primera comparecencia en autos',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'En nombre de', 'type': 'text'},
                    {'name': 'procurador', 'label': 'Procurador', 'type': 'text'},
                    {'name': 'abogado', 'label': 'Abogado', 'type': 'text'}
                ]
            },
            'poder_procesal': {
                'name': '📜 Poder para Pleitos',
                'description': 'Otorgamiento de poder procesal',
                'fields': [
                    {'name': 'poderdante', 'label': 'Poderdante', 'type': 'text'},
                    {'name': 'apoderado', 'label': 'Apoderado (Procurador)', 'type': 'text'},
                    {'name': 'dni_poderdante', 'label': 'DNI Poderdante', 'type': 'text'},
                    {'name': 'ambito', 'label': 'Ámbito del poder', 'type': 'text'}
                ]
            },
            'escrito_prueba': {
                'name': '🔬 Proposición de Prueba',
                'description': 'Escrito de proposición de medios de prueba',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'Parte que propone', 'type': 'text'},
                    {'name': 'hechos', 'label': 'Hechos a probar', 'type': 'textarea'},
                    {'name': 'pruebas', 'label': 'Medios de prueba propuestos', 'type': 'textarea'}
                ]
            },
            'burofax': {
                'name': '📮 Burofax',
                'description': 'Comunicación fehaciente por burofax',
                'fields': [
                    {'name': 'remitente', 'label': 'Remitente', 'type': 'text'},
                    {'name': 'destinatario', 'label': 'Destinatario', 'type': 'text'},
                    {'name': 'asunto', 'label': 'Asunto', 'type': 'text'},
                    {'name': 'contenido', 'label': 'Contenido', 'type': 'textarea'}
                ]
            },
            'requerimiento': {
                'name': '⚠️ Requerimiento Extrajudicial',
                'description': 'Requerimiento previo a reclamación judicial',
                'fields': [
                    {'name': 'requirente', 'label': 'Requirente', 'type': 'text'},
                    {'name': 'requerido', 'label': 'Requerido', 'type': 'text'},
                    {'name': 'objeto', 'label': 'Objeto del requerimiento', 'type': 'textarea'},
                    {'name': 'plazo', 'label': 'Plazo', 'type': 'text'}
                ]
            },
            'querella': {
                'name': '⚔️ Querella Criminal',
                'description': 'Escrito de querella penal',
                'fields': [
                    {'name': 'querellante', 'label': 'Querellante', 'type': 'text'},
                    {'name': 'querellado', 'label': 'Querellado', 'type': 'text'},
                    {'name': 'hechos', 'label': 'Hechos denunciados', 'type': 'textarea'},
                    {'name': 'delito', 'label': 'Delito/s', 'type': 'text'},
                    {'name': 'pruebas', 'label': 'Pruebas', 'type': 'textarea'}
                ]
            }
        }
    
    def generate_with_context(self, expediente_id, doc_type, user_instructions="", provider='ollama'):
        """Generar documento inyectando el contexto completo del expediente (v3.0.0)"""
        if not self.ai_agent:
            return self.generate(doc_type, {}, provider)

        try:
            # 1. Obtener contexto del agente
            context = self.ai_agent.get_case_context(expediente_id)
            
            # 2. Construir prompt enriquecido
            templates = self.get_templates()
            template = templates.get(doc_type, {'name': doc_type})
            
            prompt = f"""Eres un Agente Legal experto. Genera un borrador de {template['name']} basado en el siguiente contexto del expediente.
            
CONTEXTO DEL EXPEDIENTE:
{context}

⚠️ INSTRUCCIONES CRÍTICAS DE ESTILO (BASADAS EN TU APRENDIZAJE PREVIO):
Si el contexto anterior contiene la sección "DIRECTIVAS DE ESTILO APRENDIDAS", debes seguirlas estrictamente por encima de cualquier otra convención.

INSTRUCCIONES ADICIONALES DEL ABOGADO:
{user_instructions if user_instructions else "Redactar el documento siguiendo la práctica habitual española."}

Estructura el documento de forma profesional, con encabezados claros y lenguaje jurídico preciso.
Responde SOLO con el contenido del documento."""

            # 3. Generar
            result = self.ai_service.chat_cascade(prompt, mode='creative')
            
            if result.get('success'):
                content = result.get('response', '')
                return {
                    'success': True,
                    'content': content.strip(),
                    'filename': f"{doc_type}_{expediente_id}_{datetime.now().strftime('%Y%m%d')}.txt",
                    'provider': result.get('provider')
                }
            
            return {'success': False, 'error': result.get('error', 'Error en cascada')}

        except Exception as e:
            return {'success': False, 'error': str(e)}

    def generate(self, doc_type, data, provider='ollama'):
        """Generar documento usando IA"""
        try:
            templates = self.get_templates()
            
            if doc_type not in templates:
                return {'success': False, 'error': f'Tipo de documento no válido: {doc_type}'}
            
            template = templates[doc_type]
            
            # Construir prompt según el tipo
            prompt = self._build_prompt(doc_type, template, data)
            
            # Generar con IA (usar método correcto)
            if hasattr(self.ai_service, 'chat'):
                # Método chat (más compatible)
                response = self.ai_service.chat(prompt, provider=provider)
                if isinstance(response, dict):
                    content = response.get('response', '')
                else:
                    content = str(response)
            else:
                # Fallback: intentar otros métodos
                return {'success': False, 'error': 'Servicio de IA no disponible'}
            
            if not content or len(content) < 50:
                return {'success': False, 'error': 'Documento generado muy corto o vacío'}
            
            return {
                'success': True,
                'content': content.strip(),
                'filename': f"{doc_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
            }
        
        except Exception as e:
            print(f"❌ Error en generate(): {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _build_prompt(self, doc_type, template, data):
        """Construir prompt para la IA según el tipo de documento"""
        
        prompts = {
            'demanda_civil': f"""Genera una DEMANDA CIVIL profesional española con:

JUZGADO: {data.get('juzgado', 'N/A')}
DEMANDANTE: {data.get('demandante', 'N/A')}
DEMANDADO: {data.get('demandado', 'N/A')}

HECHOS:
{data.get('hechos', 'N/A')}

PETITORIO:
{data.get('petitorio', 'N/A')}

Estructura: Encabezamiento oficial, hechos numerados, fundamentos de derecho, petitorio (SUPLICO), otrosí.""",

            'contestacion_demanda': f"""Genera una CONTESTACIÓN A LA DEMANDA profesional:

PROCEDIMIENTO: {data.get('procedimiento', 'N/A')}
DEMANDADO (quien contesta): {data.get('demandado', 'N/A')}

HECHOS PROPIOS:
{data.get('hechos_propios', 'N/A')}

EXCEPCIONES Y DEFENSAS:
{data.get('excepciones', 'N/A')}

SÚPLICA:
{data.get('suplica', 'N/A')}

Estructura legal formal completa.""",

            'recurso_apelacion': f"""Genera un RECURSO DE APELACIÓN profesional:

SENTENCIA A RECURRIR: {data.get('sentencia', 'N/A')}
RECURRENTE: {data.get('recurrente', 'N/A')}

FUNDAMENTOS DE DERECHO:
{data.get('fundamentos', 'N/A')}

SÚPLICA:
{data.get('suplica', 'N/A')}

Estructura: Encabezamiento, fundamentos jurídicos numerados, petitorio.""",

            'recurso_reposicion': f"""Genera un RECURSO DE REPOSICIÓN profesional:

PROCEDIMIENTO: {data.get('procedimiento', 'N/A')}
RESOLUCIÓN RECURRIDA: {data.get('resolucion', 'N/A')}
RECURRENTE: {data.get('recurrente', 'N/A')}

MOTIVOS DEL RECURSO:
{data.get('motivos', 'N/A')}

Formato legal completo.""",

            'escrito_alegaciones': f"""Genera un ESCRITO DE ALEGACIONES profesional:

PROCEDIMIENTO: {data.get('procedimiento', 'N/A')}
EN NOMBRE DE: {data.get('parte', 'N/A')}

ALEGACIONES:
{data.get('alegaciones', 'N/A')}

Estructura formal.""",

            'desistimiento': f"""Genera un DESISTIMIENTO legal profesional:

PROCEDIMIENTO: {data.get('procedimiento', 'N/A')}
PARTE QUE DESISTE: {data.get('parte', 'N/A')}

MOTIVO:
{data.get('motivo', 'Por convenir a mis intereses.')}

Desistimiento formal del procedimiento.""",

            'personacion': f"""Genera una PERSONACIÓN Y SOLICITUD DE COPIAS:

PROCEDIMIENTO: {data.get('procedimiento', 'N/A')}
EN NOMBRE DE: {data.get('parte', 'N/A')}
PROCURADOR: {data.get('procurador', 'N/A')}
ABOGADO: {data.get('abogado', 'N/A')}

Primera comparecencia formal en autos.""",

            'poder_procesal': f"""Genera un PODER PARA PLEITOS profesional:

PODERDANTE: {data.get('poderdante', 'N/A')}
APODERADO (Procurador): {data.get('apoderado', 'N/A')}
DNI PODERDANTE: {data.get('dni_poderdante', 'N/A')}
ÁMBITO DEL PODER: {data.get('ambito', 'N/A')}

Poder notarial completo para representación procesal.""",

            'escrito_prueba': f"""Genera una PROPOSICIÓN DE PRUEBA profesional:

PROCEDIMIENTO: {data.get('procedimiento', 'N/A')}
PARTE QUE PROPONE: {data.get('parte', 'N/A')}

HECHOS A PROBAR:
{data.get('hechos', 'N/A')}

MEDIOS DE PRUEBA:
{data.get('pruebas', 'N/A')}

Proposición formal de pruebas (documental, testifical, pericial).""",

            'burofax': f"""Genera un BUROFAX LEGAL profesional:

REMITENTE:
{data.get('remitente', 'N/A')}

DESTINATARIO:
{data.get('destinatario', 'N/A')}

ASUNTO: {data.get('asunto', 'N/A')}

CONTENIDO:
{data.get('contenido', 'N/A')}

Formato oficial de burofax notarial fehaciente. Incluir fecha y datos de firmantes.""",

            'requerimiento': f"""Genera un REQUERIMIENTO EXTRAJUDICIAL profesional:

REQUIRENTE: {data.get('requirente', 'N/A')}
REQUERIDO: {data.get('requerido', 'N/A')}
PLAZO: {data.get('plazo', 'N/A')}

OBJETO DEL REQUERIMIENTO:
{data.get('objeto', 'N/A')}

Requerimiento formal previo a acción judicial.""",

            'querella': f"""Genera una QUERELLA CRIMINAL profesional:

QUERELLANTE: {data.get('querellante', 'N/A')}
QUERELLADO: {data.get('querellado', 'N/A')}
DELITO/S: {data.get('delito', 'N/A')}

HECHOS DENUNCIADOS:
{data.get('hechos', 'N/A')}

PRUEBAS:
{data.get('pruebas', 'N/A')}

Escrito de querella criminal con fundamentos penales.""",
        }
        
        if doc_type in prompts:
            return prompts[doc_type]
        else:
            # Prompt genérico para cualquier tipo no previsto
            fields_text = "\n".join([f"{k.upper()}: {v}" for k, v in data.items() if v])
            return f"""Genera un documento legal profesional tipo {template.get('name', doc_type)}:

{fields_text}

Usa formato formal, estructura clara y lenguaje jurídico apropiado."""
