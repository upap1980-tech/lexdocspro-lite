import unittest
from services.ai_agent_service import AIAgentService
from services.ai_service import AIService
from models import DatabaseManager
import os

class TestFeedbackLoopEVO(unittest.TestCase):
    def setUp(self):
        self.db = DatabaseManager()
        self.ai = AIService()
        self.agent = AIAgentService(self.ai, self.db)
        self.expediente_id = "TEST-EVO-001"
        
        # Limpiar datos previos de test si existen
        self.db.registrar_log('debug', 'test', f"Iniciando test EVO para {self.expediente_id}")

    def test_learning_cycle(self):
        print("\n🧠 Iniciando Ciclo de Aprendizaje EVO...")
        
        # 1. Agregar feedback negativo sobre estilo
        print("📝 Paso 1: Agregando feedback sobre exceso de lenguaje pasivo...")
        self.db.add_case_note(
            expediente_id=self.expediente_id,
            contenido="Evitar el uso de la voz pasiva. Prefiero un lenguaje más directo y asertivo.",
            tipo='feedback_ia',
            score=-1
        )
        
        # 2. Agregar otro feedback sobre estructura
        print("📝 Paso 2: Agregando feedback sobre el suplico...")
        self.db.add_case_note(
            expediente_id=self.expediente_id,
            contenido="En el suplico, siempre desglosar los intereses legales de forma explícita.",
            tipo='feedback_ia',
            score=-1
        )
        
        # 3. Verificar consolidación
        print("🔍 Paso 3: Verificando consolidación de aprendizaje...")
        directives = self.agent.consolidate_learning(self.expediente_id)
        print(f"Directivas aprendidas:\n{directives}")
        
        self.assertIsNotNone(directives)
        self.assertTrue(len(directives) > 10)
        
        # 4. Verificar inyección en contexto
        context = self.agent.get_case_context(self.expediente_id)
        self.assertIn("DIRECTIVAS DE ESTILO APRENDIDAS", context)
        print("✅ Aprendizaje inyectado correctamente en el contexto del agente.")

if __name__ == '__main__':
    unittest.main()
