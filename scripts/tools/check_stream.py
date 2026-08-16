from __future__ import annotations

import asyncio
import json
import os
import sys
import time
from uuid import uuid4

import httpx

from xiaosu.core.config import get_settings


async def main() -> None:
    settings = get_settings()
    secret = settings.admin_password or settings.admin_token
    if secret is None:
        raise SystemExit("ADMIN_PASSWORD or ADMIN_TOKEN is required.")
    base_url = os.getenv("XIAOSU_API_URL", "http://127.0.0.1:8000/api/v1")
    payload = {
        "message": sys.argv[1] if len(sys.argv) > 1 else "你好，请用三句话介绍你自己",
        "platform": "web",
        "tenant_id": "stream-check",
        "conversation_id": str(uuid4()),
        "user_id": "verification",
        "user_name": "流式验证",
    }
    delta_count = 0
    character_count = 0
    started = time.perf_counter()
    async with httpx.AsyncClient(base_url=base_url, timeout=90) as client:
        login = await client.post(
            "/auth/login",
            json={
                "username": settings.admin_username,
                "password": secret.get_secret_value(),
            },
        )
        login.raise_for_status()
        async with client.stream("POST", "/chat/stream", json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                event = json.loads(line[6:])
                elapsed = time.perf_counter() - started
                if event["type"] == "delta":
                    delta_count += 1
                    character_count += len(event.get("content", ""))
                    print(
                        f"{elapsed:6.2f}s delta #{delta_count} "
                        f"cumulative_chars={character_count}",
                        flush=True,
                    )
                else:
                    print(
                        f"{elapsed:6.2f}s {event['type']} "
                        f"{event.get('stage', '')} {event.get('label', '')}",
                        flush=True,
                    )
    if delta_count < 2:
        raise SystemExit(f"Expected multiple delta events, received {delta_count}.")


if __name__ == "__main__":
    asyncio.run(main())
