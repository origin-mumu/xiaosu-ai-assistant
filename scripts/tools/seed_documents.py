from __future__ import annotations

import os
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
DOCUMENTS = ROOT / "data" / "documents"


def load_local_env() -> dict[str, str]:
    values: dict[str, str] = {}
    path = ROOT / ".env"
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8-sig").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def main() -> None:
    local_env = load_local_env()
    base_url = os.getenv("XIAOSU_API_URL", "http://localhost:8000/api/v1").rstrip("/")
    username = os.getenv("ADMIN_USERNAME") or local_env.get("ADMIN_USERNAME") or "admin"
    password = (
        os.getenv("ADMIN_PASSWORD")
        or os.getenv("ADMIN_TOKEN")
        or local_env.get("ADMIN_PASSWORD")
        or local_env.get("ADMIN_TOKEN")
    )
    if not password:
        raise SystemExit("ADMIN_PASSWORD or ADMIN_TOKEN is required to seed documents.")

    with httpx.Client(base_url=base_url, timeout=120) as client:
        login = client.post(
            "/auth/login", json={"username": username, "password": password}
        )
        login.raise_for_status()
        for path in sorted(DOCUMENTS.iterdir()):
            if not path.is_file():
                continue
            with path.open("rb") as source:
                response = client.post(
                    "/documents",
                    files={"file": (path.name, source, "application/octet-stream")},
                )
            response.raise_for_status()
            result = response.json()
            document = result["document"]
            print(
                f"{path.name} -> {result['action']} / {document['status']} / "
                f"{document['chunk_count']} chunks"
            )


if __name__ == "__main__":
    main()
