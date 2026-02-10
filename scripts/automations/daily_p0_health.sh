#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
mkdir -p reports
TS="$(date +%Y%m%d_%H%M%S)"
OUT="reports/daily_p0_health_${TS}.log"
{
  echo "[INFO] Daily P0 Health - ${TS}"
  ./.venv312/bin/python scripts/p0_skills/api_contract_skill.py || true
  ./.venv312/bin/python scripts/p0_skills/frontend_integrity_skill.py || true
  ./.venv312/bin/python scripts/p0_skills/route_coverage_skill.py || true
  ./.venv312/bin/python -m unittest tests/test_smoke_routes.py
} | tee "$OUT"
echo "[OK] Report: $OUT"
