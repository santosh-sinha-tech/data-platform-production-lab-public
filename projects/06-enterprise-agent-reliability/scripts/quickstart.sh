#!/bin/sh
set -eu
cd "$(dirname "$0")/.."
docker build -t project06-agent-lab:local .
docker run --rm project06-agent-lab:local python -m pytest -q
mkdir -p runtime/quick
docker run --rm -v "$PWD/runtime/quick:/output" project06-agent-lab:local python -m agent_lab.experiments --mode quick --output /output
