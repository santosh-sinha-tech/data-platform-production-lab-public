#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker build -t project06-agent-lab:local .
docker run --rm project06-agent-lab:local python -m pytest -q
mkdir -p results
docker run --rm -v "$PWD/results:/output" project06-agent-lab:local python -m agent_lab.experiments --mode full --output /output
docker run --rm -v "$PWD/results:/output:ro" project06-agent-lab:local python scripts/verify_artifacts.py /output
