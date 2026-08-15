import asyncio
import json
from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.agent.schemas import ChatRequest, ChatResponse
from xiaosu.agent.service import ChatService
from xiaosu.api.auth import require_admin
from xiaosu.core.config import Settings, get_settings
from xiaosu.db.session import get_session

router = APIRouter(prefix="/chat", tags=["chat"], dependencies=[Depends(require_admin)])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]
SettingsDependency = Annotated[Settings, Depends(get_settings)]


@router.post("/completions", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> ChatResponse:
    return await ChatService(session, settings).chat(request)


@router.post("/stream")
async def stream_chat(
    request: ChatRequest,
    session: SessionDependency,
    settings: SettingsDependency,
) -> StreamingResponse:
    result = await ChatService(session, settings).chat(request)

    async def events() -> AsyncIterator[str]:
        for start in range(0, len(result.answer), 8):
            payload = {"type": "delta", "content": result.answer[start : start + 8]}
            yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.015)
        completed = {"type": "done", "data": result.model_dump(mode="json")}
        yield f"data: {json.dumps(completed, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        events(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
