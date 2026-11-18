#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD/src${PYTHONPATH:+:$PYTHONPATH}"
export SPARK_LOCAL_IP="${SPARK_LOCAL_IP:-127.0.0.1}"
python -m pytest -q
python -m small_files.cli --config "${1:-config/quick.json}" "${@:2}"
