#!/usr/bin/env bash
set -euo pipefail
BASE="${1:-http://127.0.0.1:5002}"
check_header(){
  local h="$1"
  if curl -sSI "$BASE/api/health" | rg -i "^${h}:" >/dev/null; then
    echo "[OK] ${h}"
  else
    echo "[WARN] Missing ${h}"
  fi
}
check_header "X-Content-Type-Options"
check_header "X-Frame-Options"
check_header "Content-Security-Policy"
check_header "X-Request-ID"
