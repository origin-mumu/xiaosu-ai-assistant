from typing import Annotated

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.agent.schemas import MessageLogResponse
from xiaosu.api.auth import require_admin
from xiaosu.core.config import Settings, get_settings
from xiaosu.db.models import Conversation, Message
from xiaosu.db.session import get_session

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


class SettingsUpdate(BaseModel):
    llm_model: str = Field(min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9._-]+$")


@router.get("/messages", response_model=list[MessageLogResponse])
async def list_messages(
    session: SessionDependency,
    limit: Annotated[int, Query(ge=1, le=500)] = 100,
) -> list[MessageLogResponse]:
    rows = await session.execute(
        select(Message, Conversation)
        .join(Conversation)
        .order_by(Message.created_at.desc())
        .limit(limit)
    )
    return [
        MessageLogResponse(
            id=message.id,
            conversation_id=conversation.id,
            platform=conversation.platform,
            external_user_id=conversation.external_user_id,
            user_name=conversation.user_name,
            role=message.role,
            content=message.content,
            status=message.status,
            model=message.model,
            prompt_tokens=message.prompt_tokens,
            completion_tokens=message.completion_tokens,
            cost=float(message.cost),
            latency_ms=message.latency_ms,
            tool_calls=message.tool_calls,
            citations=message.citations,
            error_code=message.error_code,
            created_at=message.created_at,
        )
        for message, conversation in rows
    ]


@router.get("/settings")
async def settings_status(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    key = settings.dashscope_api_key
    dingtalk_id = settings.dingtalk_client_id
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "embedding_model": settings.embedding_model,
        "embedding_dimension": settings.embedding_dimension,
        "model_api_key_configured": bool(key and key.get_secret_value()),
        "dingtalk_configured": bool(
            dingtalk_id
            and dingtalk_id.get_secret_value()
            and settings.dingtalk_client_secret
            and settings.dingtalk_client_secret.get_secret_value()
        ),
        "retrieval_top_k": settings.retrieval_top_k,
        "retrieval_min_score": settings.retrieval_min_score,
    }


@router.patch("/settings")
async def update_settings(
    request: SettingsUpdate,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    settings.llm_model = request.llm_model
    return {"llm_model": settings.llm_model, "persistence": "until_process_restart"}
