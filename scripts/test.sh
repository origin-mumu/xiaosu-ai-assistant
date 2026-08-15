#!/usr/bin/env bash
set -euo pipefail

(
  cd apps/api
  uv run pytest
  uv run ruff check src tests
)

pnpm typecheck

