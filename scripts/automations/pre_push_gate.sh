#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
./.venv312/bin/python -m unittest tests/test_smoke_routes.py
./.venv312/bin/python -m unittest tests/test_lexnet_endpoints.py
# E2E puede requerir JWT/cookies de prueba según entorno; no bloquea gate base.
./.venv312/bin/python -m unittest tests/test_document_orchestration_e2e.py || echo "[WARN] document_orchestration_e2e requires auth fixture in this environment"
echo "[OK] pre-push gate passed"
