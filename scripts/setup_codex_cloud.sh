#!/usr/bin/env bash
set -euo pipefail
cd "$(git rev-parse --show-toplevel)"
if [ ! -x .venv/bin/python ]; then uv venv --python 3.12 .venv; fi
uv pip install --python .venv/bin/python 'jsonschema==4.26.0'
printf '%s\n' 'ChemDraw architecture-contract environment ready; native execution is a separate gate.'
