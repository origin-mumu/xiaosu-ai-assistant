#!/usr/bin/env bash
set -euo pipefail

(
  cd apps/api
  uv run ruff check src tests
  uv run ruff format --check src tests
)

pnpm typecheck

