from dataclasses import dataclass, field
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, Field

from xiaosu.knowledge.schemas import Citation


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    platform: Literal["web", "dingtalk"] = "web"
    tenant_id: str = "default"
    conversation_id: str = "default"
    user_id: str = "admin"
    user_name: str | None = None


class ChatResponse(BaseModel):
    conversation_uuid: UUID
    message_id: UUID
    answer: str
    citations: list[Citation]
    tool_calls: list[dict[str, object]]
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: int
    status: str


class MessageLogResponse(BaseModel):
    id: UUID
    conversation_id: UUID
    platform: str
    external_user_id: str
    user_name: str | None
    role: str
    content: str
    status: str
    model: str | None
    prompt_tokens: int
    completion_tokens: int
    cost: float
    latency_ms: int
    tool_calls: list[dict[str, object]]
    citations: list[dict[str, object]]
    error_code: str | None
    created_at: datetime


class MessageUserOption(BaseModel):
    value: str
    label: str


class QuestionAnswerLogResponse(BaseModel):
    question: MessageLogResponse
    answer: MessageLogResponse | None = None


class MessagePageResponse(BaseModel):
    items: list[QuestionAnswerLogResponse]
    total: int
    page: int
    page_size: int
    users: list[MessageUserOption]


class ToolCallLogResponse(BaseModel):
    id: str
    message_id: UUID
    conversation_id: UUID
    platform: str
    external_user_id: str
    user_name: str | None
    tool_name: str
    arguments: dict[str, object]
    result: object
    duration_ms: int | None = None
    success: bool
    created_at: datetime


class ToolCallPageResponse(BaseModel):
    items: list[ToolCallLogResponse]
    total: int
    page: int
    page_size: int
    tool_names: list[str]


class ToolDefinitionResponse(BaseModel):
    id: str
    name: str
    description: str
    category: str
    parameters: list[str]
    enabled: bool = True


@dataclass(slots=True)
class AgentToolCall:
    id: str
    name: str
    arguments: dict[str, object]


@dataclass(slots=True)
class ModelTurn:
    content: str = ""
    tool_calls: list[AgentToolCall] = field(default_factory=list)
    prompt_tokens: int = 0
    completion_tokens: int = 0


@dataclass(slots=True)
class ModelStreamEvent:
    type: Literal["content", "done"]
    content: str = ""
    turn: ModelTurn | None = None


@dataclass(slots=True)
class AgentStreamEvent:
    type: Literal["status", "delta", "done"]
    stage: str | None = None
    label: str | None = None
    detail: str | None = None
    phase: Literal["start", "complete"] | None = None
    tool_name: str | None = None
    arguments: dict[str, object] | None = None
    tool_result: object | None = None
    content: str = ""
    result: "AgentResult | None" = None


@dataclass(slots=True)
class AgentResult:
    answer: str
    citations: list[Citation]
    tool_calls: list[dict[str, object]]
    prompt_tokens: int
    completion_tokens: int
    status: Literal["completed", "unanswered"] = "completed"
