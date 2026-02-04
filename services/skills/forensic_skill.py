class ForensicStyleSkill:
    """
    Skill para aplicar estilo forense/jurídico a textos.
    Define el 'Tone of Voice' del asistente legal.
    """
    
    SYSTEM_PROMPT_ADDENDUM = """
    DIRECTRICES DE ESTILO FORENSE (OBLIGATORIO):
    1. Usa terminología jurídica precisa (LEC, CP, CC).
    2. Mantén un tono formal, objetivo y respetuoso ("Su Señoría", "La parte actora").
    3. Estructura lógica: Hechos -> Fundamentos de Derecho -> Suplico/Conclusión.
    4. Cita artículos de ley específicos cuando sea posible.
    5. Evita coloquialismos y ambigüedades.
    """
    
    PATTERNS = {
        'demanda': "AL JUZGADO DE PRIMERA INSTANCIA DE...",
        'recurso': "A LA SALA...",
        'escrito_tramite': "DIGO: Que por medio del presente escrito..."
    }

    def enhance_prompt(self, base_prompt):
        """Inyecta directrices forenses al prompt"""
        return f"{base_prompt}\n\n{self.SYSTEM_PROMPT_ADDENDUM}"
    
    def get_template(self, doc_type):
        return self.PATTERNS.get(doc_type, "")
