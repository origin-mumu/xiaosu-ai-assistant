import json
from datetime import UTC, datetime
from pathlib import Path
from threading import Event

HEARTBEAT_FILENAME = "dingtalk-heartbeat.json"
HEARTBEAT_INTERVAL_SECONDS = 20
HEARTBEAT_STALE_SECONDS = 75


def heartbeat_path(log_dir: Path) -> Path:
    return log_dir / HEARTBEAT_FILENAME


def write_heartbeat(log_dir: Path, stop_event: Event) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    path = heartbeat_path(log_dir)
    while not stop_event.is_set():
        payload = {"timestamp": datetime.now(UTC).isoformat(), "status": "running"}
        path.write_text(json.dumps(payload), encoding="utf-8")
        stop_event.wait(HEARTBEAT_INTERVAL_SECONDS)


def read_im_status(log_dir: Path, configured: bool) -> dict[str, object]:
    path = heartbeat_path(log_dir)
    heartbeat_at: datetime | None = None
    if path.is_file():
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
            heartbeat_at = datetime.fromisoformat(str(payload["timestamp"]))
        except (ValueError, KeyError, json.JSONDecodeError):
            heartbeat_at = None
    age = (datetime.now(UTC) - heartbeat_at).total_seconds() if heartbeat_at else None
    connected = bool(configured and age is not None and age <= HEARTBEAT_STALE_SECONDS)
    return {
        "channel": "dingtalk",
        "configured": configured,
        "connected": connected,
        "status": "运行中" if connected else ("服务未运行" if configured else "待配置"),
        "last_heartbeat_at": heartbeat_at.isoformat() if heartbeat_at else None,
    }
