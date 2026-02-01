"""
Generador de documentos legales con IA
"""

class DocumentGenerator:
    def __init__(self, ai_service):
        self.ai_service = ai_service
    
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
            'escrito_alegaciones': {
                'name': '📝 Escrito de Alegaciones',
                'description': 'Respuesta a trámite de alegaciones',
                'fields': [
                    {'name': 'procedimiento', 'label': 'Nº Procedimiento', 'type': 'text'},
                    {'name': 'parte', 'label': 'En nombre de', 'type': 'text'},
                    {'name': 'alegaciones', 'label': 'Alegaciones', 'type': 'textarea'}
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
                    {'name': 'ambito', 'label': 'Ámbito del poder', 'type': 'select', 'options': ['General', 'Específico para este pleito']}
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
    
    def generate(self, doc_type, data, provider='ollama'):
        """Generar documento usando IA"""
        
        templates = self.get_templates()
        
        if doc_type not in templates:
            raise ValueError(f"Tipo de documento no válido: {doc_type}")
        
        template = templates[doc_type]
        
        # Construir prompt según el tipo
        prompt = self._build_prompt(doc_type, template, data)
        
        # Generar con IA
        response = self.ai_service.generar_documento(prompt, provider)
        
        return response
    
    def _build_prompt(self, doc_type, template, data):
        """Construir prompt para la IA según el tipo de documento"""
        
        prompts = {
            'demanda_civil': f"""
Genera una DEMANDA CIVIL profesional con la siguiente información:

JUZGADO: {data.get('juzgado')}
DEMANDANTE: {data.get('demandante')}
DEMANDADO: {data.get('demandado')}

HECHOS:
{data.get('hechos')}

PETITORIO:
{data.get('petitorio')}

Estructura completa: Encabezamiento, Hechos numerados, Fundamentos de Derecho con jurisprudencia, Petitorio (SUPLICO), Otrosí (documentos).
""",
            
            'contestacion_demanda': f"""
Genera una CONTESTACIÓN A LA DEMANDA profesional con:

PROCEDIMIENTO: {data.get('procedimiento')}
DEMANDADO (que contesta): {data.get('demandado')}

HECHOS PROPIOS:
{data.get('hechos_propios')}

EXCEPCIONES Y DEFENSAS:
{data.get('excepciones')}

SÚPLICA:
{data.get('suplica')}

Incluye: Encabezamiento, Hechos numerados, Fundamentos de Derecho (defensa), Súplica solicitando desestimación de la demanda.
""",

            'recurso_reposicion': f"""
Genera un RECURSO DE REPOSICIÓN profesional:

PROCEDIMIENTO: {data.get('procedimiento')}
RESOLUCIÓN RECURRIDA: {data.get('resolucion')}
RECURRENTE: {data.get('recurrente')}

MOTIVOS DEL RECURSO:
{data.get('motivos')}

Estructura: Encabezamiento, Antecedentes, Motivos del recurso con fundamentación jurídica, Súplica de revocación.
""",

            'desistimiento': f"""
Genera un ESCRITO DE DESISTIMIENTO profesional:

PROCEDIMIENTO: {data.get('procedimiento')}
PARTE QUE DESISTE: {data.get('parte')}
MOTIVO: {data.get('motivo', 'Por convenir a mis intereses')}

Incluye: Encabezamiento formal, manifestación clara del desistimiento, súplica de archivo.
""",

            'personacion': f"""
Genera un ESCRITO DE PERSONACIÓN Y SOLICITUD DE COPIAS:

PROCEDIMIENTO: {data.get('procedimiento')}
EN NOMBRE DE: {data.get('parte')}
PROCURADOR: {data.get('procurador')}
ABOGADO: {data.get('abogado')}

Incluye: Personación formal, acreditación de representación, solicitud de copias, domicilio procesal.
""",

            'poder_procesal': f"""
Genera un PODER PARA PLEITOS profesional:

PODERDANTE: {data.get('poderdante')}
DNI: {data.get('dni_poderdante')}
APODERADO: {data.get('apoderado')}
ÁMBITO: {data.get('ambito')}

Texto notarial completo con facultades procesales: comparecer, demandar, contestar, recursos, transigir, etc.
""",

            'escrito_prueba': f"""
Genera un ESCRITO DE PROPOSICIÓN DE PRUEBA:

PROCEDIMIENTO: {data.get('procedimiento')}
PARTE: {data.get('parte')}

HECHOS A PROBAR:
{data.get('hechos')}

MEDIOS DE PRUEBA:
{data.get('pruebas')}

Estructura: Encabezamiento, Hechos controvertidos, Pruebas propuestas (documental, testifical, pericial), Súplica de admisión.
""",

            'querella': f"""
Genera una QUERELLA CRIMINAL profesional:

QUERELLANTE: {data.get('querellante')}
QUERELLADO: {data.get('querellado')}
DELITO/S: {data.get('delito')}

HECHOS:
{data.get('hechos')}

PRUEBAS:
{data.get('pruebas')}

Incluye: Encabezamiento, Hechos narrados cronológicamente, Fundamentos jurídicos (tipificación penal), Pruebas, Responsabilidad civil, Súplica.
"""
        }
        
        # Usar prompt específico o genérico
        if doc_type in prompts:
            return prompts[doc_type]
        else:
            # Prompt genérico para otros tipos
            fields_text = "\n".join([f"{k.upper()}: {v}" for k, v in data.items()])
            return f"""
Genera un documento legal profesional tipo {template['name']} con la siguiente información:

{fields_text}

Usa formato formal, estructura clara y lenguaje jurídico apropiado.
"""
