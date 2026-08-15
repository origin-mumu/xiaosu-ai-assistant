import json
import logging
from contextvars import ContextVar
from datetime import UTC, datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from uuid import uuid4

request_id_context: ContextVar[str] = ContextVar("request_id", default="-")


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, object] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": request_id_context.get(),
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    root = logging.getLogger()
    if any(getattr(handler, "_xiaosu_handler", False) for handler in root.handlers):
        return

    root.setLevel(logging.INFO)
    formatter = JsonFormatter()

    console = logging.StreamHandler()
    console.setFormatter(formatter)
    console._xiaosu_handler = True  # type: ignore[attr-defined]

    app_file = RotatingFileHandler(
        log_dir / "app.jsonl",
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding="utf-8",
    )
    app_file.setFormatter(formatter)
    app_file._xiaosu_handler = True  # type: ignore[attr-defined]

    root.addHandler(console)
    root.addHandler(app_file)


def new_request_id() -> str:
    return uuid4().hex
