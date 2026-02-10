#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
LOGFILE="${1:-reports/daily_p0_health_latest.log}"
if [[ ! -f "$LOGFILE" ]]; then
  echo "[WARN] Log not found: $LOGFILE"
  exit 0
fi
echo "[INFO] 5xx/traceback triage from $LOGFILE"
rg -n " 5[0-9][0-9] |Traceback|ERROR|Exception" "$LOGFILE" || echo "[OK] No critical patterns found"
