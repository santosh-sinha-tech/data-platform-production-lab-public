#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
RAG_PYTHON="${RAG_PYTHON:-python}"
RAG_MODE="${1:-quick}"
case "$RAG_MODE" in
  quick|full) ;;
  *) echo 'Usage: bash scripts/run.sh [quick|full]' >&2; exit 2 ;;
esac
RAG_TEST_DENSE=1 "$RAG_PYTHON" -m pytest -q
"$RAG_PYTHON" -m rag_lab.runner --mode "$RAG_MODE" --output "results/local-${RAG_MODE}"
"$RAG_PYTHON" scripts/validate_reports.py "results/local-${RAG_MODE}"
