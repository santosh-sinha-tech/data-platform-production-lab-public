#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
export PYTHONPATH=src
python -m pytest -q
python scripts/benchmark.py
python scripts/scenarios.py
python scripts/validate_results.py
