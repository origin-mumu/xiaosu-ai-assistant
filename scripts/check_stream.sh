#!/usr/bin/env bash
set -euo pipefail

uv run --project apps/api python scripts/tools/check_stream.py "$@"
