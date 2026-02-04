# LexDocsPro ENTERPRISE v3.0 - Configuración Centralizada
import os
from pathlib import Path

# Directorios base
BASE_DIR = Path(__file__).parent
EXPEDIENTES_DIR = Path.home() / "Desktop" / "EXPEDIENTES_LEXDOCS"
GENERADOS_DIR = BASE_DIR / "GENERADOS"
PENDIENTES_DIR = Path.home() / "Desktop" / "PENDIENTES_LEXDOCS"

# Crear directorios si no existen
for dir_path in [EXPEDIENTES_DIR, GENERADOS_DIR, PENDIENTES_DIR]:
    dir_path.mkdir(parents=True, exist_ok=True)

# IA Providers (cascada privacidad-first)
IA_PROVIDERS = [
    {"name": "Ollama Local", "api_url": "http://localhost:11434", "model": "lexdocs-legal-pro", "priority": 1},
    {"name": "Groq (Llama 3.2)", "api_key": os.getenv("GROQ_API_KEY"), "priority": 2},
    {"name": "Perplexity", "api_key": os.getenv("PERPLEXITY_API_KEY"), "priority": 3},
    {"name": "OpenAI GPT-4o-mini", "api_key": os.getenv("OPENAI_API_KEY"), "priority": 4}
]

# LexNET Plazos (festivos Canarias 2026)
FESTIVOS_CANARIAS_2026 = [
    "2026-01-01", "2026-01-06", "2026-03-19", "2026-04-17", "2026-05-01", "2026-07-07",
    "2026-08-15", "2026-09-15", "2026-10-12", "2026-11-01", "2026-12-06", "2026-12-08", "2026-12-25"
]

# BD SQLite (Fase 2)
DB_PATH = BASE_DIR / "lexdocs.db"
SECRET_KEY = os.getenv("SECRET_KEY", "lexdocs-enterprise-2026-dev")

# Autoprocesar
AUTOPROCESAR_PATH = str(PENDIENTES_DIR)
AUTOPROCESAR_LOG = BASE_DIR / "autoprocesar.log"

print(f"📁 EXPEDIENTES: {EXPEDIENTES_DIR}")
print(f"📁 GENERADOS: {GENERADOS_DIR}")
print(f"📁 PENDIENTES: {PENDIENTES_DIR}")
print(f"🗄️ BD: {DB_PATH}")
