#!/usr/bin/env bash
set -euo pipefail

base_url="${XIAOSU_API_URL:-http://localhost:8000/api/v1}"

for file in data/documents/*; do
  echo "Uploading ${file}"
  curl --fail --silent --show-error \
    --form "file=@${file}" \
    "${base_url}/documents" >/dev/null
done

echo "Sample documents uploaded. Check indexing status in the Web console."
