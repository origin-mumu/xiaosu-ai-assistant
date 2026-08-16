#!/usr/bin/env bash
set -euo pipefail

(
  cd apps/api
  uv run python ../../scripts/tools/generate_samples.py
)
