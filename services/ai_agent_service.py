"""
AI Agent Service - Orquestador de inteligencia contextual (v3.0.0)
Coordina la recolección de contexto de la DB y documentos previos para una generación inteligente.
"""
import os
import json
from datetime import datetime
from typing import List, Dict, Optional

class AIAgentService:
    def __init__(self, ai_service, db_manager):
        self.ai = ai_service
        self.db = db_manager
        self.memory_limit = 5 # Documentos previos a consultar

    def consolidate_learning(self, expediente_id: str) -> str:
        """
        Analiza todo el feedback acumulado para un expediente y genera 
        un "Manual de Estilo" o directivas consolidadas (v3.0.0 EVO).
        """
        all_notes = self.db.get_notas_by_expediente(expediente_id)
        feedback = [n for n in all_notes if n.get('tipo') == 'feedback_ia']
        
        if not feedback:
            return ""
            
        # Orquestar un prompt para que la IA resuma las lecciones aprendidas
        feedback_history = "\n".join([f"- {n.get('contenido')}" for n in feedback])
        
        prompt = f"""Analiza el siguiente historial de correcciones hechas por un abogado a borradores generados por IA.
Extrae REGLAS DE ESTILO y PREFERENCIAS DE CONTENIDO que la IA debe seguir en este expediente específico.

CORRECCIONES:
{feedback_history}

Responde con una lista corta de directivas claras (ej: "No usar lenguaje pasivo", "Ser más directo en el suplico").
Si no hay suficientes datos para extraer reglas, responde "Mantener estilo estándar"."""

        result = self.ai.chat_cascade(prompt, mode='creative')
        if result.get('success'):
            return result.get('response', "").strip()
        return ""

    def get_case_context(self, expediente_id: str) -> str:
        """
        Recuperar el contexto completo de un expediente para la IA.
        Combina metadata de la DB, historial y DIRECTIVAS APRENDIDAS (v3.0.0 EVO).
        """
        context_parts = []
        
        # 1. Obtener datos básicos del expediente
        case_data = self.db.get_expediente(expediente_id)
        if case_data:
            context_parts.append(f"EXPEDIENTE: {case_data.get('numero', 'N/A')}")
            context_parts.append(f"CLIENTE: {case_data.get('cliente', 'N/A')}")
            context_parts.append(f"JUZGADO: {case_data.get('juzgado', 'N/A')}")
            context_parts.append(f"RESUMEN CASO: {case_data.get('resumen', 'Sin resumen')}")

        # 2. APRENDIZAJE CONSOLIDADO (Prioridad v3.0.0 EVO)
        learned_directives = self.consolidate_learning(expediente_id)
        if learned_directives and "Mantener estilo estándar" not in learned_directives:
            context_parts.append("\n⚠️ DIRECTIVAS DE ESTILO APRENDIDAS (OBEDECER PRIORITARIAMENTE):")
            context_parts.append(learned_directives)

        # 3. Obtener documentos previos (historial corto)
        docs = self.db.get_documentos_by_expediente(expediente_id, limit=3)
        if docs:
            context_parts.append("\nRESUMEN DE HISTORIAL:")
            for d in docs:
                context_parts.append(f"- {d.get('fecha')}: {d.get('tipo')} ({d.get('resumen', 'Sin resumen')})")

        return "\n".join(context_parts)

    def propose_next_action(self, context: str) -> Dict:
        """El agente analiza el contexto y sugiere qué documento redactar"""
        prompt = f"""Analiza el siguiente contexto de un expediente legal y sugiere la PRÓXIMA ACCIÓN necesaria (ej: presentar recurso, contestar demanda, pedir prueba).

CONTEXTO:
{context}

Responde SOLO en JSON:
{{
  "sugerencia": "título de la acción",
  "razonamiento": "por qué es necesaria esta acción",
  "urgencia": "alta/media/baja",
  "tipo_documento_id": "id_del_template"
}}"""
        
        result = self.ai.chat_cascade(prompt, mode='creative')
        if result.get('success'):
            try:
                # Extraer JSON de la respuesta
                import re
                json_match = re.search(r'\{[^{}]*\}', result['response'], re.DOTALL)
                if json_match:
                    return json.loads(json_match.group())
            except: pass
            
        return {"sugerencia": "Revisar expediente", "razonamiento": "No se pudo determinar acción automática", "urgencia": "media"}

    def generate_draft(self, expediente_id: str, doc_type: str, user_instructions: str = ""):
        """Generar un borrador de documento inyectando el contexto completo del expediente"""
        context = self.get_case_context(expediente_id)
        
        # Este método será usado por el DocumentGenerator refactoreado
        return {
            "expediente_id": expediente_id,
            "context": context,
            "doc_type": doc_type,
            "instructions": user_instructions
        }
