#!/usr/bin/env bash
set -euo pipefail

uv run --project apps/api python scripts/tools/seed_documents.py

echo "Sample documents uploaded. Check indexing status in the Web console."
