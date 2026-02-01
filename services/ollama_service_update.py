# Agregar al final del __init__ de OllamaService:

# Modelos disponibles por orden de preferencia
self.models_priority = [
    'lexdocs-legal-pro',   # Optimizado tras pruebas
    'lexdocs-legal',        # Actual
    'lexdocs-llama3',       # Alternativa
    'mistral',              # Base
    'llama3'                # Genérico
]

# Usar primer modelo disponible
available = self.get_available_models()
for preferred in self.models_priority:
    if preferred in available:
        self.model = preferred
        print(f"✅ Usando modelo: {self.model}")
        break
