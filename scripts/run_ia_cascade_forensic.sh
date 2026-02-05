#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

MIN_SUCCESS_RATE="${MIN_SUCCESS_RATE:-60}"
MAX_P95_MS="${MAX_P95_MS:-130000}"
MAX_5XX="${MAX_5XX:-0}"

echo "== IA Cascade Forensic Runner =="
echo "Root: $ROOT_DIR"
echo "Thresholds: success>=$MIN_SUCCESS_RATE%, p95<=$MAX_P95_MS ms, 5xx<=$MAX_5XX"

python3 scripts/audit_enterprise_modules.py
python3 scripts/ia_cascade_slo_guard.py \
  --root . \
  --min-success-rate "$MIN_SUCCESS_RATE" \
  --max-p95-ms "$MAX_P95_MS" \
  --max-5xx "$MAX_5XX"

echo "Forensic runner PASS"
echo "Reports:"
echo "- reports/enterprise_modules_audit.json"
echo "- reports/ia_cascade_slo_guard.json"
