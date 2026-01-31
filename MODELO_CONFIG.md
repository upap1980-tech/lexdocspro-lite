# Configuración del Modelo IA

## Modelo Activo: lexdocs-legal-pro

### Razones de Selección
- ✅ **Precisión superior**: 100% respuestas correctas vs 0% del anterior
- ✅ **Cita artículos reales**: Art. 404.1 LEC, no inventa normativa
- ✅ **Plazos correctos**: 20 días hábiles (correcto) vs 10 días (incorrecto)
- ✅ **Sin timeouts**: Responde casos complejos

### Parámetros Optimizados
- Temperature: 0.25 (muy preciso)
- Context: 8,192 tokens (documentos largos)
- Top-p: 0.88 (determinista)
- Num_predict: 2,500 (respuestas completas)

### Pruebas Realizadas (31/01/2026)
1. **Consulta simple**: ✅ CORRECTO
2. **Análisis plazo**: ✅ CORRECTO (art. 404.1 LEC)
3. **Caso práctico**: ✅ CORRECTO (LAU 29/1994)

### Modelos Disponibles
- **lexdocs-legal-pro** ← ACTIVO (recomendado)
- lexdocs-legal (descartado: cita normativa falsa)
- lexdocs-llama3 (menos preciso)
- llama3 (genérico)
- mistral (base)

### Última actualización
31 de enero de 2026
