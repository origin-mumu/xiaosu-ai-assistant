from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator
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
    llm_provider: Literal["dashscope"] = "dashscope"
    dashscope_api_key: SecretStr | None = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen3.7-plus"
    embedding_model: str = "qwen3.7-text-embedding"
    embedding_dimension: int = 1024

    @field_validator("embedding_dimension")
    @classmethod
    def validate_embedding_dimension(cls, value: int) -> int:
        allowed_dimensions = {256, 512, 768, 1024, 1536, 2048, 2560}
        if value not in allowed_dimensions:
            raise ValueError(f"embedding_dimension must be one of {sorted(allowed_dimensions)}")
        return value


@lru_cache
def get_settings() -> Settings:
    return Settings()
