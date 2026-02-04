"""
Test interactivo para AIAgentService v3.0.0
"""
import os
import sys

# Añadir directorio raíz al path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import DatabaseManager
from services.ai_service import AIService
from services.ai_agent_service import AIAgentService
from services.document_generator import DocumentGenerator

def test_ai_agent():
    print("🚀 Iniciando Test AI Agent v3.0.0...")
    
    # 1. Setup
    db = DatabaseManager('lexdocs_test_agent.db')
    ai = AIService()
    agent = AIAgentService(ai, db)
    gen = DocumentGenerator(ai, agent)
    
    # 2. Crear datos de prueba (Expediente y Documentos)
    print("📂 Creando expediente de prueba...")
    exp_id = db.create_expediente(
        numero="JU-2026/001",
        cliente="Juan Pérez",
        contrario="Seguros Atlas S.A.",
        juzgado="1ª Instancia nº 5 de Madrid",
        resumen="Reclamación de daños por accidente de tráfico ocurrido el 15/01/2026."
    )
    
    # Añadir nota de estrategia
    db.add_case_note(exp_id, "El contrario ha ofrecido una indemnización mínima. Proceder con demanda.")
    
    # Añadir documento previo simulado
    db.create_saved_document(
        filename="oferta_aseguradora.pdf",
        file_path="/path/to/doc.pdf",
        client_name="Juan Pérez",
        doc_type="Oferta",
        expedient="JU-2026/001"
    )
    
    # 3. Verificar contexto
    print("🔍 Recuperando contexto...")
    context = agent.get_case_context(exp_id)
    print("--- CONTEXTO DETECTADO ---")
    print(context)
    print("--------------------------")
    
    # 4. Probar generación con contexto
    print("📝 Generando borrador de demanda con contexto...")
    result = gen.generate_with_context(
        expediente_id=exp_id,
        doc_type="demanda_civil",
        user_instructions="Enfocar en la responsabilidad civil de la aseguradora según el historial."
    )
    
    if result['success']:
        print("✅ Borrador generado con éxito!")
        print(f"🤖 Proveedor: {result.get('provider')}")
        print("\n--- INICIO BORRADOR ---")
        # Mostrar solo los primeros 200 caracteres para el log
        print(result['content'][:500] + "...")
        print("--- FIN BORRADOR ---")
    else:
        print(f"❌ Error en generación: {result['error']}")

if __name__ == "__main__":
    if os.path.exists('lexdocs_test_agent.db'):
        os.remove('lexdocs_test_agent.db')
    test_ai_agent()
