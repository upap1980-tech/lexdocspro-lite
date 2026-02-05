from __future__ import annotations

from datetime import datetime
from typing import Dict, List

from services.skills.deadline_skill import DeadlineSkill
from services.skills.forensic_skill import ForensicStyleSkill
from services.skills.rag_skill import LiteRAGSkill


class BusinessSkillsService:
    """Orquesta skills de negocio legal por jurisdicción y tipo documental."""

    def __init__(self, db_manager):
        self.db = db_manager
        self.deadline = DeadlineSkill()
        self.forensic = ForensicStyleSkill()
        self.rag = LiteRAGSkill(db_manager)

    def list_jurisdictions(self) -> List[Dict]:
        return [
            {"id": "ES_GENERAL", "name": "España (General)", "scope": "Nacional"},
            {"id": "ES_CANARIAS", "name": "Canarias", "scope": "Autonómico"},
            {"id": "ES_MADRID", "name": "Madrid", "scope": "Autonómico"},
        ]

    def list_document_templates(self, jurisdiction: str = "ES_GENERAL") -> List[Dict]:
        base_templates = [
            {"doc_type": "demanda", "title": "Demanda inicial", "tone": "forense"},
            {"doc_type": "recurso", "title": "Recurso", "tone": "forense"},
            {"doc_type": "escrito_tramite", "title": "Escrito de trámite", "tone": "forense"},
        ]
        if jurisdiction == "ES_CANARIAS":
            base_templates.append(
                {"doc_type": "lexnet_urgente", "title": "Escrito urgente LexNET", "tone": "urgente"}
            )
        return base_templates

    def build_strategy(self, payload: Dict) -> Dict:
        query = payload.get("query", "")
        jurisdiction = payload.get("jurisdiction", "ES_GENERAL")
        doc_type = payload.get("doc_type", "escrito_tramite")
        fecha_notificacion = payload.get("fecha_notificacion")
        plazo_dias = int(payload.get("plazo_dias", 0) or 0)

        deadline = None
        if fecha_notificacion and plazo_dias > 0:
            try:
                dt = datetime.strptime(fecha_notificacion, "%Y-%m-%d")
                deadline = self.deadline.calculate(dt, plazo_dias, tipo="habil")
            except Exception:
                deadline = None

        forensic_template = self.forensic.get_template(doc_type)
        prompt_base = (
            f"Jurisdicción: {jurisdiction}\n"
            f"Tipo documental: {doc_type}\n"
            f"Objetivo: {query or 'Preparar estrategia procesal'}"
        )
        styled_prompt = self.forensic.enhance_prompt(prompt_base)
        context = self.rag.retrieve_context(query, w_limit=3) if query else ""

        return {
            "jurisdiction": jurisdiction,
            "doc_type": doc_type,
            "forensic_template": forensic_template,
            "styled_prompt": styled_prompt,
            "deadline": deadline,
            "rag_context": context,
            "recommended_steps": [
                "Validar hechos y pretensión principal",
                "Revisar competencia y procedimiento aplicable",
                "Estructurar fundamentos jurídicos y prueba",
                "Redactar suplico y peticiones accesorias",
            ],
        }
