# Smoke mínimo (P0)

Fecha: 2026-02-06

## Comandos
1. Arranque:
   - `./start_LexDocsPro-LITE.sh` (puertos 5002/5174)
   - `./start_produccion.sh` (modo producción, host 0.0.0.0)
2. Validación P0 runtime:
   - `./.venv312/bin/python scripts/validate_p0_runtime.py`

## Criterio de salida
- `reports/p0_runtime_validation.json` con `ok: true`.
- `/api/health` responde 200.
- Sin 500 en LexNET/OCR/IA básicos.
