from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.core.config import get_settings
from xiaosu.db.session import get_session

router = APIRouter(tags=["health"])


class HealthResponse(BaseModel):
    status: str
    service: str
    timestamp: datetime


class DependencyHealthResponse(BaseModel):
    status: str
    database: str
    llm_provider: str
    llm_model: str
    embedding_model: str
    embedding_dimension: int
    model_api_key_configured: bool


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(
        status="ok",
        service="xiaosu-api",
        timestamp=datetime.now(UTC),
    )


@router.get("/health/dependencies", response_model=DependencyHealthResponse)
async def dependency_health(
    session: Annotated[AsyncSession, Depends(get_session)],
) -> DependencyHealthResponse:
    await session.execute(text("SELECT 1"))
    settings = get_settings()
    key_configured = bool(
        settings.dashscope_api_key and settings.dashscope_api_key.get_secret_value()
    )
    return DependencyHealthResponse(
        status="ok",
        database="ok",
        llm_provider=settings.llm_provider,
        llm_model=settings.llm_model,
        embedding_model=settings.embedding_model,
        embedding_dimension=settings.embedding_dimension,
        model_api_key_configured=key_configured,
    )
