# Resumen Sesión - Auto-procesamiento Documentos LexNET

## ✅ Completado

1. **Sistema de monitoreo automático** (`auto_procesar.py`)
   - Detecta archivos en carpeta PENDIENTES
   - Analiza con IA (Ollama) + OCR
   - Extrae cliente, tipo documento, fecha
   - Guarda organizadamente

2. **Mejoras al análisis de documentos**
   - Regex para extraer nombres (D., Dª, Don, Doña)
   - Detección de tipo documento (notificación, demanda, sentencia, etc.)
   - Extracción de fecha del nombre archivo
   - Fallback a IA si no detecta con regex

3. **Problema detectado**
   - Script AppleScript antiguo interfiere
   - Se abre ventana Editor de Scripts
   - Solución: cambiar carpeta monitoreada

## 📁 Archivos clave

- `/Desktop/PROYECTOS/LexDocsPro-LITE/auto_procesar.py`
- `/Desktop/PROYECTOS/LexDocsPro-LITE/run.py` (endpoint smart-analyze mejorado)
- Carpeta monitoreada: `~/Desktop/PENDIENTES_LEXDOCS`

## 🔄 Siguiente paso

- Desactivar AppleScript viejo o usar carpeta separada
- Probar sistema completo de procesamiento automático
