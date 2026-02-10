# Plan de Ejecucion Produccion (P0 -> P1 -> P2)

## P0 Bloqueante
- Arranque estable backend/frontend con puertos fijos y `/api/health` + `/api/health/ready`.
- Seguridad minima activa: headers, request-id/correlation-id, rate limit endpoints sensibles.
- Flujo legal principal operativo: LexNET + Documentos E2E + OCR + AutoProcesador.
- Smoke en verde: `tests/test_smoke_routes.py`.

## P1 Recomendado
- Endurecer auth/rbac y cerrar credenciales hardcoded.
- Logging centralizado con triage de errores.
- Regression suites por modulo legal (LexNET, E2E, IA cascade, firma).

## P2 Mejora continua
- SLOs por endpoint/proveedor (latencia, error rate).
- Reporte de release readiness automatizado.
- Verificacion periodica backup/restore.

## Automatizaciones implementadas
- `scripts/automations/daily_p0_health.sh`
- `scripts/automations/coverage_drift_alert.sh`
- `scripts/automations/lexnet_regression_suite.sh`
- `scripts/automations/db_schema_guard.sh`
- `scripts/automations/error_log_triage.sh`
- `scripts/automations/security_baseline_check.sh`
- `scripts/automations/pre_push_gate.sh`
- `scripts/automations/release_readiness_report.sh`
- `scripts/automations/backup_verification.sh`
- `scripts/automations/contract_drift_frontend_backend.sh`

## Skills negocio sugeridas
- Plantillas procesales por jurisdiccion y fase.
- Priorizacion automatica de plazos criticos.
- QA legal de documentos antes de firma/envio.
