from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env", "../../.env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = 8000
    web_origin: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://xiaosu:xiaosu@localhost:5432/xiaosu"
    log_dir: Path = Field(default=Path("logs"))


@lru_cache
def get_settings() -> Settings:
    return Settings()
