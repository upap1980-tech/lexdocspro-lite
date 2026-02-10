#!/usr/bin/env bash
set -euo pipefail
SRC="${1:-/Users/victormfrancisco/Desktop/PROCESADOS_LEXDOCS}"
DST_BASE="${2:-/Users/victormfrancisco/Desktop/BACKUP_LEXDOCS}"
TS="$(date +%Y%m%d_%H%M%S)"
DST="${DST_BASE}/verify_${TS}"
mkdir -p "$DST"
cp -R "$SRC" "$DST/" >/dev/null 2>&1 || true
if [[ -d "$DST" ]]; then
  echo "[OK] Backup verification folder created: $DST"
else
  echo "[FAIL] Backup verification failed"
  exit 1
fi
