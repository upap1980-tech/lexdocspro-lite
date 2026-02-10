#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p reports
TS="$(date +%Y%m%d_%H%M%S)"
OUT="reports/release_readiness_${TS}.md"
{
  echo "# Release Readiness ${TS}"
  echo
  echo "## Checks"
  ./scripts/automations/db_schema_guard.sh || true
  ./scripts/automations/security_baseline_check.sh || true
  ./.venv312/bin/python -m unittest tests/test_smoke_routes.py || true
  echo
  echo "## Risks"
  echo "- Verificar firma digital PDF en entorno real con certificado final"
  echo "- Validar SMTP real y alertas de plazos críticos"
  echo "- Confirmar backup/restore con muestra real"
} > "$OUT"
echo "[OK] $OUT"
