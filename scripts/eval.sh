#!/usr/bin/env bash
set -euo pipefail

(
  cd apps/api
  uv run python evals/run_evals.py "$@"
)
