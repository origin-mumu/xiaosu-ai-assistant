#!/usr/bin/env bash
set -euo pipefail

(
  cd apps/api
  uv run ruff check src tests evals
  uv run ruff format --check src tests evals
)

pnpm typecheck
