#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m pytest
PYTHONPATH=src .venv/bin/python -m ai_observability.benchmark --mode quick
