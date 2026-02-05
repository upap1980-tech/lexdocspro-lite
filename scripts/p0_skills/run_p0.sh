#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"

echo "== P0 Skills =="
python3 "$ROOT_DIR/scripts/p0_skills/api_contract_skill.py" --root "$ROOT_DIR" || true
python3 "$ROOT_DIR/scripts/p0_skills/frontend_integrity_skill.py" --root "$ROOT_DIR"
python3 "$ROOT_DIR/scripts/p0_skills/route_coverage_skill.py" --root "$ROOT_DIR"
python3 "$ROOT_DIR/scripts/p0_skills/smoke_p0.py" --root "$ROOT_DIR"

echo "P0 checks completados."
