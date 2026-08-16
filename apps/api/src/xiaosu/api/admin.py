from typing import Annotated, Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from xiaosu.agent.schemas import (
    MessageLogResponse,
    MessagePageResponse,
    MessageUserOption,
    QuestionAnswerLogResponse,
    ToolCallLogResponse,
    ToolCallPageResponse,
    ToolDefinitionResponse,
)
from xiaosu.agent.sources import tool_display_name
from xiaosu.agent.tools import TOOL_DEFINITIONS
from xiaosu.api.auth import require_admin
from xiaosu.core.config import Settings, get_settings
from xiaosu.core.runtime import load_runtime_configuration, save_runtime_configuration
from xiaosu.db.models import Conversation, Message
from xiaosu.db.session import get_session
from xiaosu.im.status import read_im_status

router = APIRouter(prefix="/admin", tags=["admin"], dependencies=[Depends(require_admin)])
SessionDependency = Annotated[AsyncSession, Depends(get_session)]


class SettingsUpdate(BaseModel):
    llm_provider: Literal["dashscope", "zhipuai"] | None = None
    llm_model: str | None = Field(default=None, min_length=2, max_length=100, pattern=r"^[a-zA-Z0-9._-]+$")


class KnowledgeSettingsUpdate(BaseModel):
    chunk_size: int = Field(ge=200, le=4000)
    chunk_overlap: int = Field(ge=0, le=1000)
    retrieval_top_k: int = Field(ge=1, le=20)
    retrieval_min_score: float = Field(ge=0, le=1)
    max_upload_mb: int = Field(ge=1, le=100)
    embedding_batch_size: int = Field(ge=1, le=50)
    duplicate_policy: Literal["replace", "skip"]


@router.get("/messages", response_model=MessagePageResponse)
async def list_messages(
    session: SessionDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=500)] = 20,
    platform: Annotated[str | None, Query(pattern=r"^(web|dingtalk)$")] = None,
    user_id: str | None = None,
    message_status: Annotated[
        str | None, Query(alias="status", pattern=r"^(completed|unanswered|failed)$")
    ] = None,
) -> MessagePageResponse:
    answer_alias = aliased(Message)
    next_question_alias = aliased(Message)
    next_question_at = (
        select(next_question_alias.created_at)
        .where(
            next_question_alias.conversation_id == Message.conversation_id,
            next_question_alias.role == "user",
            next_question_alias.created_at > Message.created_at,
        )
        .order_by(next_question_alias.created_at.asc())
        .limit(1)
        .correlate(Message)
        .scalar_subquery()
    )
    answer_id = (
        select(answer_alias.id)
        .where(
            answer_alias.conversation_id == Message.conversation_id,
            answer_alias.role == "assistant",
            answer_alias.created_at >= Message.created_at,
            or_(next_question_at.is_(None), answer_alias.created_at < next_question_at),
        )
        .order_by(answer_alias.created_at.asc(), answer_alias.id.asc())
        .limit(1)
        .correlate(Message)
        .scalar_subquery()
    )
    answer_status = (
        select(answer_alias.status)
        .where(answer_alias.id == answer_id)
        .correlate(Message)
        .scalar_subquery()
    )

    conditions = [Message.role == "user"]
    if platform:
        conditions.append(Conversation.platform == platform)
    if user_id:
        conditions.append(Conversation.external_user_id == user_id)
    if message_status:
        conditions.append(func.coalesce(answer_status, "unanswered") == message_status)

    total = await session.scalar(
        select(func.count(Message.id)).join(Conversation).where(*conditions)
    )
    rows = await session.execute(
        select(Message, Conversation)
        .join(Conversation)
        .where(*conditions)
        .order_by(Message.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    user_rows = await session.execute(
        select(Conversation.external_user_id, func.max(Conversation.user_name))
        .group_by(Conversation.external_user_id)
        .order_by(func.max(Conversation.user_name), Conversation.external_user_id)
    )
    question_rows = list(rows)
    question_ids = [message.id for message, _ in question_rows]
    answer_links: dict[object, object] = {}
    answers: dict[object, Message] = {}
    if question_ids:
        link_rows = await session.execute(
            select(Message.id, answer_id).where(Message.id.in_(question_ids))
        )
        answer_links = {
            question_id: linked_answer_id
            for question_id, linked_answer_id in link_rows
            if linked_answer_id is not None
        }
        if answer_links:
            answer_rows = await session.execute(
                select(Message).where(Message.id.in_(answer_links.values()))
            )
            answers = {message.id: message for message in answer_rows.scalars()}

    def serialize(message: Message, conversation: Conversation) -> MessageLogResponse:
        return MessageLogResponse(
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

    items = []
    for question, conversation in question_rows:
        answer = answers.get(answer_links.get(question.id))
        items.append(
            QuestionAnswerLogResponse(
                question=serialize(question, conversation),
                answer=serialize(answer, conversation) if answer else None,
            )
        )
    users = [
        MessageUserOption(value=external_user_id, label=user_name or external_user_id)
        for external_user_id, user_name in user_rows
    ]
    return MessagePageResponse(
        items=items,
        total=total or 0,
        page=page,
        page_size=page_size,
        users=users,
    )


@router.get("/tool-calls", response_model=ToolCallPageResponse)
async def list_tool_calls(
    session: SessionDependency,
    page: Annotated[int, Query(ge=1)] = 1,
    page_size: Annotated[int, Query(ge=1, le=200)] = 20,
    platform: Annotated[str | None, Query(pattern=r"^(web|dingtalk)$")] = None,
    tool_name: str | None = None,
    success: bool | None = None,
) -> ToolCallPageResponse:
    conditions = [
        Message.role == "assistant",
        func.json_array_length(Message.tool_calls) > 0,
    ]
    if platform:
        conditions.append(Conversation.platform == platform)
    rows = await session.execute(
        select(Message, Conversation)
        .join(Conversation)
        .where(*conditions)
        .order_by(Message.created_at.desc())
    )

    items: list[ToolCallLogResponse] = []
    available_names: set[str] = set()
    for message, conversation in rows:
        for index, call in enumerate(message.tool_calls):
            name = str(call.get("name", "unknown"))
            available_names.add(name)
            result = call.get("result")
            call_success = bool(
                call.get(
                    "success",
                    not (isinstance(result, dict) and "error" in result),
                )
            )
            if tool_name and name != tool_name:
                continue
            if success is not None and call_success != success:
                continue
            raw_duration = call.get("duration_ms")
            items.append(
                ToolCallLogResponse(
                    id=f"{message.id}:{index}",
                    message_id=message.id,
                    conversation_id=conversation.id,
                    platform=conversation.platform,
                    external_user_id=conversation.external_user_id,
                    user_name=conversation.user_name,
                    tool_name=name,
                    arguments=call.get("arguments", {}),
                    result=result,
                    duration_ms=int(raw_duration) if raw_duration is not None else None,
                    success=call_success,
                    created_at=message.created_at,
                )
            )

    total = len(items)
    start = (page - 1) * page_size
    return ToolCallPageResponse(
        items=items[start : start + page_size],
        total=total,
        page=page,
        page_size=page_size,
        tool_names=sorted(available_names),
    )


@router.get("/tools", response_model=list[ToolDefinitionResponse])
async def list_tools() -> list[ToolDefinitionResponse]:
    categories = {
        "search_knowledge": "知识库",
        "find_employee": "员工信息",
        "get_employee": "员工信息",
        "query_attendance": "考勤",
        "query_orders": "订单",
        "get_current_time": "系统",
    }
    parameter_names = {
        "query": "查询内容",
        "name": "员工姓名",
        "employee_id": "员工编号",
        "start_date": "开始日期",
        "end_date": "结束日期",
        "timezone": "时区",
    }
    items = []
    for definition in TOOL_DEFINITIONS:
        function = definition["function"]
        name = str(function["name"])
        parameter_schema = function.get("parameters", {})
        properties = parameter_schema.get("properties", {})
        parameters = [
            str(value.get("description") or parameter_names.get(key, "业务参数"))
            for key, value in properties.items()
        ]
        items.append(
            ToolDefinitionResponse(
                id=name,
                name=tool_display_name(name),
                description=str(function.get("description", "")),
                category=categories.get(name, "其他"),
                parameters=parameters,
            )
        )
    return items


@router.get("/settings")
async def settings_status(
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, object]:
    runtime = await load_runtime_configuration(session, settings)
    dashscope_configured = bool(settings.dashscope_api_key and settings.dashscope_api_key.get_secret_value())
    zhipuai_configured = bool(settings.zhipuai_api_key and settings.zhipuai_api_key.get_secret_value())
    dingtalk_id = settings.dingtalk_client_id
    dingtalk_configured = bool(
        dingtalk_id
        and dingtalk_id.get_secret_value()
        and settings.dingtalk_client_secret
        and settings.dingtalk_client_secret.get_secret_value()
    )
    current_key_configured = zhipuai_configured if settings.llm_provider == "zhipuai" else dashscope_configured
    model_options = [
        model.strip()
        for model in settings.llm_model_options.split(",")
        if model.strip()
    ]
    if settings.llm_model not in model_options:
        model_options.insert(0, settings.llm_model)

    providers_info = {
        "dashscope": {
            "name": "阿里百炼 (DashScope)",
            "configured": dashscope_configured,
            "models": [m.strip() for m in settings.dashscope_model_options.split(",") if m.strip()],
            "embedding_model": settings.dashscope_embedding_model,
        },
        "zhipuai": {
            "name": "智谱清言 (ZhipuAI)",
            "configured": zhipuai_configured,
            "models": [m.strip() for m in settings.zhipuai_model_options.split(",") if m.strip()],
            "embedding_model": settings.zhipuai_embedding_model,
        },
    }

    return {
        "llm_provider": settings.llm_provider,
        "llm_providers": ["dashscope", "zhipuai"],
        "providers_info": providers_info,
        "llm_model": settings.llm_model,
        "llm_model_options": model_options,
        "embedding_model": settings.embedding_model,
        "embedding_dimension": settings.embedding_dimension,
        "model_api_key_configured": current_key_configured,
        "dashscope_configured": dashscope_configured,
        "zhipuai_configured": zhipuai_configured,
        "dingtalk_configured": dingtalk_configured,
        "im_status": read_im_status(settings.log_dir, dingtalk_configured),
        **runtime.model_dump(mode="json"),
    }


@router.patch("/settings")
async def update_settings(
    request: SettingsUpdate,
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str]:
    await load_runtime_configuration(session, settings)
    if request.llm_provider:
        settings.llm_provider = request.llm_provider
        if request.llm_provider == "zhipuai":
            settings.embedding_model = settings.zhipuai_embedding_model
            settings.llm_model_options = settings.zhipuai_model_options
            if not request.llm_model:
                settings.llm_model = "glm-4-plus"
        else:
            settings.embedding_model = settings.dashscope_embedding_model
            settings.llm_model_options = settings.dashscope_model_options
            if not request.llm_model:
                settings.llm_model = "qwen3.7-plus"

    if request.llm_model:
        settings.llm_model = request.llm_model

    await save_runtime_configuration(session, settings)
    return {
        "llm_provider": settings.llm_provider,
        "llm_model": settings.llm_model,
        "persistence": "database",
    }


@router.patch("/settings/knowledge")
async def update_knowledge_settings(
    request: KnowledgeSettingsUpdate,
    session: SessionDependency,
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, int | float | str]:
    if request.chunk_overlap >= request.chunk_size:
        raise HTTPException(status_code=422, detail="分块重叠长度必须小于分块长度")
    settings.chunk_size = request.chunk_size
    settings.chunk_overlap = request.chunk_overlap
    settings.retrieval_top_k = request.retrieval_top_k
    settings.retrieval_min_score = request.retrieval_min_score
    settings.max_upload_bytes = request.max_upload_mb * 1024 * 1024
    settings.embedding_batch_size = request.embedding_batch_size
    settings.duplicate_policy = request.duplicate_policy
    await save_runtime_configuration(session, settings)
    return {
        **request.model_dump(),
        "persistence": "database",
    }
