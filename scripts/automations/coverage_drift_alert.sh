#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
THRESHOLD="${1:-65}"
FILE="reports/route_coverage_summary.json"
if [[ ! -f "$FILE" ]]; then
  echo "[WARN] No coverage summary found: $FILE"
  exit 0
fi
RATE=$(python3 - <<'PY'
import json
p='reports/route_coverage_summary.json'
try:
  d=json.load(open(p))
  print(float(d.get('coverage_percent',0)))
except Exception:
  print(0)
PY
)
RATE_INT=${RATE%.*}
if (( RATE_INT < THRESHOLD )); then
  echo "[ALERT] Coverage drift: ${RATE}% < ${THRESHOLD}%"
  exit 2
fi
echo "[OK] Coverage: ${RATE}%"
