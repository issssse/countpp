#!/usr/bin/env bash
set -euo pipefail

uv venv --clear .venv
source .venv/bin/activate

uv pip install \
  -e packages/schemas \
  -e packages/signal_io \
  -e packages/extractors \
  -e services/label_studio_bridge \
  -e services/extraction_worker \
  -e services/data_api \
  -e services/analysis_engine \
  httpx \
  pytest \
  ruff \
  pyright

npm --prefix apps/workbench_web ci
