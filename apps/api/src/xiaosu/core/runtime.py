from typing import Literal

from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.core.config import Settings
from xiaosu.db.models import RuntimeSetting

RUNTIME_SETTINGS_KEY = "application"


class RuntimeConfiguration(BaseModel):
    llm_provider: Literal["dashscope", "zhipuai"] = "dashscope"
    llm_model: str = Field(min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9._-]+$")
    chunk_size: int = Field(ge=200, le=4000)
    chunk_overlap: int = Field(ge=0, le=1000)
    retrieval_top_k: int = Field(ge=1, le=20)
    retrieval_min_score: float = Field(ge=0, le=1)
    max_upload_mb: int = Field(ge=1, le=100)
    embedding_batch_size: int = Field(ge=1, le=50)
    duplicate_policy: Literal["replace", "skip"]

    @classmethod
    def from_settings(cls, settings: Settings) -> "RuntimeConfiguration":
        return cls(
            llm_provider=settings.llm_provider,
            llm_model=settings.llm_model,
            chunk_size=settings.chunk_size,
            chunk_overlap=settings.chunk_overlap,
            retrieval_top_k=settings.retrieval_top_k,
            retrieval_min_score=settings.retrieval_min_score,
            max_upload_mb=max(1, settings.max_upload_bytes // (1024 * 1024)),
            embedding_batch_size=settings.embedding_batch_size,
            duplicate_policy=settings.duplicate_policy,
        )

    def apply(self, settings: Settings) -> None:
        settings.llm_provider = self.llm_provider
        settings.llm_model = self.llm_model
        if self.llm_provider == "zhipuai":
            settings.llm_model_options = settings.zhipuai_model_options
        else:
            settings.llm_model_options = settings.dashscope_model_options
        if settings.embedding_provider == "zhipuai":
            settings.embedding_model = settings.zhipuai_embedding_model
        else:
            settings.embedding_model = settings.dashscope_embedding_model

        settings.chunk_size = self.chunk_size
        settings.chunk_overlap = self.chunk_overlap
        settings.retrieval_top_k = self.retrieval_top_k
        settings.retrieval_min_score = self.retrieval_min_score
        settings.max_upload_bytes = self.max_upload_mb * 1024 * 1024
        settings.embedding_batch_size = self.embedding_batch_size
        settings.duplicate_policy = self.duplicate_policy


async def load_runtime_configuration(
    session: AsyncSession,
    settings: Settings,
) -> RuntimeConfiguration:
    stored = await session.get(RuntimeSetting, RUNTIME_SETTINGS_KEY)
    configuration = (
        RuntimeConfiguration.model_validate(stored.value)
        if stored is not None
        else RuntimeConfiguration.from_settings(settings)
    )
    configuration.apply(settings)
    return configuration


async def save_runtime_configuration(
    session: AsyncSession,
    settings: Settings,
) -> RuntimeConfiguration:
    configuration = RuntimeConfiguration.from_settings(settings)
    stored = await session.get(RuntimeSetting, RUNTIME_SETTINGS_KEY)
    if stored is None:
        session.add(
            RuntimeSetting(
                key=RUNTIME_SETTINGS_KEY,
                value=configuration.model_dump(mode="json"),
            )
        )
    else:
        stored.value = configuration.model_dump(mode="json")
    await session.commit()
    return configuration
