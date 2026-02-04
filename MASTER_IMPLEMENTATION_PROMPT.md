# 🏛️ MASTER PROMPT: EVOLUCIÓN ESTRUCTURAL LEXDOCSPRO v2.3.2 -> v3.0.0

**Instrucciones para Antigravity:**
Actúa como Arquitecto de Software Principal para consolidar la versión LITE y sentar las bases de la versión Enterprise. Debes procesar las siguientes instrucciones en bloques lógicos de implementación.

---

### 🧱 NIVEL 1: ESTABILIZACIÓN Y LIMPIEZA (PRIORIDAD 0)
1. **Eliminar "Ghost Code":** Limpia `run.py` de referencias muertas a servicios Enterprise que no están físicamente en la carpeta `/services/`. Define variables como `ai_agent = None` para evitar NameErrors.
2. **Refactor de DB (SQLite Safety):** Asegura que CADA endpoint de base de datos use el patrón `db.get_connection()` con `try/except/finally`. No debe quedar ni un solo `db.conn.cursor()`.

---

### 🚀 NIVEL 2: ACTIVACIÓN DE SERVICIOS "STUBBED" (FASE LITE+)
1. **AutoProcessor v1.0:** Implementa la lógica de `AutoProcessor` para renombramiento inteligente de archivos basado en el contenido detectado por OCR/IA.
2. **SignatureService v1.0:** Activa la funcionalidad de firma digital básica (sellado de tiempo y metadatos) en documentos generados.
3. **LexNET Pro:** Refina el `LexNetAnalyzer` para que los datos extraídos se mapeen automáticamente a los modelos de `Case` y `Document` en la base de datos.

---

### 🧠 NIVEL 3: IMPLEMENTACIÓN DE SKILLS DE IA (AGENT ORCHESTRATION)
Crea una estructura modular en `services/ai_agent_service.py` para soportar:
- **Skill de Plazos:** Lógica para calcular vencimientos procesales (LEC/LECrim).
- **Skill Forense:** Inyección de prompts de sistema para adaptar el tono legal español.
- **Skill RAG:** Integración de búsqueda semántica en la carpeta de documentos del usuario.

---

### 💎 NIVEL 4: PREPARACIÓN ENTERPRISE (API & FRONTEND)
1. **Streaming Support:** Implementa el generador de Flask para respuestas `text/event-stream` en el endpoint de chat.
2. **SQLAlchemy Migration:** Crea los modelos en `models.py` usando SQLAlchemy para reemplazar el SQL crudo.
3. **API-First Refactor:** Separa las rutas de renderizado (`/`) de las rutas de datos (`/api/*`) para facilitar la migración a React.

---

### 📝 ENTREGABLES REQUERIDOS TRAS CADA BLOQUE:
1. **`UPDATE_LOG.md`:** Resumen de archivos modificados y funciones activadas.
2. **`VERIFICATION_REPORT.md`:** Resultado de tests de sintaxis y arranque de servidor.
3. **`IMPLEMENTATION_SCRIPT.sh`:** Un script consolidado para aplicar los cambios en el entorno local de forma segura.

**INICIA CON EL NIVEL 1 Y REPORTA EL PROGRESO ANTES DE AVANZAR AL SIGUIENTE.**
