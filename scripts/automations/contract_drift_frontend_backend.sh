#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
./.venv312/bin/python scripts/p0_skills/api_contract_skill.py
