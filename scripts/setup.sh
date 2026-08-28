#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-python3}"

"$PYTHON_BIN" -m venv .venv
# shellcheck disable=SC1091
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt pytest ruff

printf '\nRuralShield local environment is ready.\n'
printf 'Activate it later with: source .venv/bin/activate\n'
printf 'Run checks with: pytest -q && ruff check backend/lambda ml tests\n'
