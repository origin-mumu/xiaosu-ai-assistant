#!/usr/bin/env bash
set -euo pipefail

base_url="${XIAOSU_API_URL:-http://localhost:8000/api/v1}"
admin_username="${ADMIN_USERNAME:-}"
admin_password="${ADMIN_PASSWORD:-${ADMIN_TOKEN:-}}"

if [[ -f .env ]]; then
  while IFS='=' read -r key value; do
    value="${value%$'\r'}"
    value="${value#\"}"
    value="${value%\"}"
    value="${value#\'}"
    value="${value%\'}"
    case "${key}" in
      ADMIN_USERNAME) admin_username="${admin_username:-${value}}" ;;
      ADMIN_PASSWORD) admin_password="${admin_password:-${value}}" ;;
      ADMIN_TOKEN) admin_password="${admin_password:-${value}}" ;;
    esac
  done < <(grep -E '^(ADMIN_USERNAME|ADMIN_PASSWORD|ADMIN_TOKEN)=' .env)
fi

admin_username="${admin_username:-admin}"
if [[ -z "${admin_password}" ]]; then
  echo "ADMIN_PASSWORD or ADMIN_TOKEN is required to seed documents." >&2
  exit 1
fi

cookie_file="$(mktemp)"
trap 'rm -f "${cookie_file}"' EXIT
login_payload="$(python -c 'import json, sys; print(json.dumps({"username": sys.argv[1], "password": sys.argv[2]}))' "${admin_username}" "${admin_password}")"

curl --fail --silent --show-error \
  --cookie-jar "${cookie_file}" \
  --header "Content-Type: application/json" \
  --data "${login_payload}" \
  "${base_url}/auth/login" >/dev/null

for file in data/documents/*; do
  echo "Uploading ${file}"
  curl --fail --silent --show-error \
    --cookie "${cookie_file}" \
    --form "file=@${file}" \
    "${base_url}/documents" >/dev/null
done

echo "Sample documents uploaded. Check indexing status in the Web console."
