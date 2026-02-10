#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../.."
./.venv312/bin/python -m unittest tests/test_lexnet_endpoints.py tests/test_lexnet_parser.py
