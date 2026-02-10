#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PY="${ROOT_DIR}/.venv312/bin/python"

if [[ ! -x "$PY" ]]; then
  echo "❌ No encuentro el runtime .venv312 en ${PY}"
  echo "👉 Crea/activa el entorno y vuelve a intentar."
  exit 1
fi

export PYTHONUNBUFFERED=1
export PYTHONPATH="${ROOT_DIR}"
export HOST="0.0.0.0"
export PORT="5002"

exec "$PY" "${ROOT_DIR}/run.py" "$@"
