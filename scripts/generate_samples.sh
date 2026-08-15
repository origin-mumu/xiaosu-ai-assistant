#!/usr/bin/env bash
set -euo pipefail

(
  cd apps/api
  uv run python ../../scripts/generate_samples.py
)
