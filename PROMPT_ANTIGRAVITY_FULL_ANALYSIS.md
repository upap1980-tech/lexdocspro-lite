# 🧪 PROMPT DE ANÁLISIS EXHAUSTIVO - LEXDOCSPRO LITE v2.3.2

**Instrucciones para Antigravity:**
Actúa como un Ingeniero de Software Senior especializado en Flask y React para realizar un análisis de "Salud Total" del proyecto LexDocsPro LITE tras la recuperación Hotfix v2.3.2.

### 📋 FASE 1: MAPEO DE DEPENDENCIAS Y "GHOST CODE"
1. **Analizar `run.py` de arriba a abajo:**
   - Detectar todos los imports de servicios que no existen en la carpeta `/services/`.
   - Identificar variables "huérfanas" (como `ai_agent`, `ai_agent_service`) que están causando NameErrors.
   - Verificar la coherencia entre los objetos instanciados (ej. `DocumentGenerator`, `LexNetService`) y los archivos físicos en el sistema.

### 🔍 FASE 2: AUDITORÍA DE BASE DE DATOS Y CONEXIONES
1. **Verificar el patrón de conexión:**
   - Analizar si quedan remanentes de `db.conn.cursor()` en cualquier parte del código (no solo en dashboard).
   - Validar que todos los bloques `try/except/finally` para la base de datos están correctamente indentados y cierran la conexión.
   - Comprobar la compatibilidad con `models.py` (v3.0.0 PRO detectada en logs).

### 🛡️ FASE 3: AUDITORÍA DE SEGURIDAD Y DECORADORES
1. **Mapear la superficie de ataque:**
   - Listar todos los `@app.route` que no tengan `@jwt_required_custom`.
   - Reportar cuáles de estos endpoints manejan datos sensibles o servicios de coste (IA).
   - Validar la lógica del decorador en `decorators.py`.

### 🎨 FASE 4: VALIDACIÓN DE FRONTEND (UI/UX)
1. **Analizar `templates/index.html`:**
   - ¿Es la versión Enterprise v3.0 compatible con el `app.js` de la versión LITE?
   - Verificar que todos los IDs (`chatPrompt`, `fileTree`, `pdfViewer`, `stats-container`) existan en el HTML para evitar errores de null en JS.

### 📝 ENTREGABLE: REPORTE DE ESTADO Y PARCHES DEFINITIVOS
Generar un archivo `FULL_HEALTH_CHECK_v232.md` que contenga:
1. **Errores Detectados:** Clasificados por severidad (Bloqueantes, Seguridad, Performance).
2. **Ghost Code Report:** Lista de funciones/servicios Enterprise que sobran en la versión LITE.
3. **Bloque de Código Fix Definitive:** Un único script de Python o Bash para limpiar `run.py` de forma permanente, eliminando los parches temporales (`# Módulo desactivado`) y dejando el código limpio y funcional.
4. **Validación de Arranque:** Pasos exactos para confirmar que el Dashboard y LexNET funcionan al 100%.

**EJECUTAR ANÁLISIS AHORA Y PRESENTAR HALLAZGOS.**
