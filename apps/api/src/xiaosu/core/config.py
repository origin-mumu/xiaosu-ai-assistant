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
    public_base_url: str = "http://localhost:5173"
    database_url: str = "postgresql+asyncpg://xiaosu:xiaosu@localhost:5432/xiaosu"
    log_dir: Path = Field(default=Path("logs"))
    upload_dir: Path = Field(default=Path("uploads"))
    max_upload_bytes: int = 20 * 1024 * 1024
    chunk_size: int = 700
    chunk_overlap: int = 100
    retrieval_top_k: int = 5
    retrieval_min_score: float = 0.35
    llm_provider: Literal["dashscope"] = "dashscope"
    dashscope_api_key: SecretStr | None = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"
    llm_model: str = "qwen3.7-plus"
    embedding_model: str = "qwen3.7-text-embedding"
    embedding_dimension: int = 1024
    agent_max_steps: int = 5
    model_timeout_seconds: float = 30
    input_price_per_million: float = 0.8
    output_price_per_million: float = 2.0
    admin_username: str = "admin"
    admin_password: SecretStr | None = None
    session_secret: SecretStr | None = None
    admin_token: SecretStr | None = None
    session_ttl_seconds: int = 8 * 60 * 60
    dingtalk_client_id: SecretStr | None = None
    dingtalk_client_secret: SecretStr | None = None
    dingtalk_robot_code: str | None = None

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
