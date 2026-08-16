from collections.abc import AsyncIterator
from decimal import Decimal
from time import perf_counter
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.agent.model import ChatModel, create_chat_model
from xiaosu.agent.runner import AgentRunner
from xiaosu.agent.schemas import ChatRequest, ChatResponse
from xiaosu.agent.tools import AgentToolExecutor
from xiaosu.core.config import Settings
from xiaosu.core.runtime import load_runtime_configuration
from xiaosu.db.base import utc_now
from xiaosu.db.models import Conversation, Message


class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        settings: Settings,
        model: ChatModel | None = None,
    ) -> None:
        self.session = session
        self.settings = settings
        self.model = model

    async def chat(self, request: ChatRequest) -> ChatResponse:
        await load_runtime_configuration(self.session, self.settings)
        started = perf_counter()
        conversation = await self._conversation(request)
        history = await self._history(conversation.id)
        self.session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content=request.message,
                status="completed",
            )
        )
        await self.session.commit()
        try:
            model = self.model or create_chat_model(self.settings)
            runner = AgentRunner(
                model,
                AgentToolExecutor(self.session, self.settings),
                self.settings.agent_max_steps,
            )
            result = await runner.run(history, request.message)
            latency_ms = int((perf_counter() - started) * 1000)
            cost = self._cost(result.prompt_tokens, result.completion_tokens)
            message = Message(
                id=uuid4(),
                conversation_id=conversation.id,
                role="assistant",
                content=result.answer,
                status=result.status,
                model=self.settings.llm_model,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                cost=cost,
                latency_ms=latency_ms,
                tool_calls=result.tool_calls,
                citations=[citation.model_dump(mode="json") for citation in result.citations],
            )
            self.session.add(message)
            conversation.last_active_at = utc_now()
            await self.session.commit()
            return ChatResponse(
                conversation_uuid=conversation.id,
                message_id=message.id,
                answer=result.answer,
                citations=result.citations,
                tool_calls=result.tool_calls,
                prompt_tokens=result.prompt_tokens,
                completion_tokens=result.completion_tokens,
                cost=float(cost),
                latency_ms=latency_ms,
                status=result.status,
            )
        except Exception as error:
            await self.session.rollback()
            latency_ms = int((perf_counter() - started) * 1000)
            friendly = "小苏暂时无法连接模型服务，请稍后重试或联系管理员检查 API Key。"
            message = Message(
                id=uuid4(),
                conversation_id=conversation.id,
                role="assistant",
                content=friendly,
                status="failed",
                model=self.settings.llm_model,
                latency_ms=latency_ms,
                error_code=type(error).__name__,
            )
            self.session.add(message)
            await self.session.commit()
            return ChatResponse(
                conversation_uuid=conversation.id,
                message_id=message.id,
                answer=friendly,
                citations=[],
                tool_calls=[],
                prompt_tokens=0,
                completion_tokens=0,
                cost=0,
                latency_ms=latency_ms,
                status="failed",
            )

    async def stream_chat(self, request: ChatRequest) -> AsyncIterator[dict[str, object]]:
        await load_runtime_configuration(self.session, self.settings)
        started = perf_counter()
        conversation = await self._conversation(request)
        history = await self._history(conversation.id)
        self.session.add(
            Message(
                conversation_id=conversation.id,
                role="user",
                content=request.message,
                status="completed",
            )
        )
        await self.session.commit()
        try:
            model = self.model or create_chat_model(self.settings)
            runner = AgentRunner(
                model,
                AgentToolExecutor(self.session, self.settings),
                self.settings.agent_max_steps,
            )
            async for event in runner.stream(history, request.message):
                if event.type == "status":
                    yield {
                        "type": "status",
                        "stage": event.stage or "working",
                        "label": event.label or "正在处理",
                        "detail": event.detail,
                        "phase": event.phase,
                    }
                    continue
                if event.type == "delta":
                    yield {"type": "delta", "content": event.content}
                    continue
                result = event.result
                if result is None:
                    raise RuntimeError("Agent 流未返回结果")
                latency_ms = int((perf_counter() - started) * 1000)
                cost = self._cost(result.prompt_tokens, result.completion_tokens)
                message = Message(
                    id=uuid4(),
                    conversation_id=conversation.id,
                    role="assistant",
                    content=result.answer,
                    status=result.status,
                    model=self.settings.llm_model,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    cost=cost,
                    latency_ms=latency_ms,
                    tool_calls=result.tool_calls,
                    citations=[citation.model_dump(mode="json") for citation in result.citations],
                )
                self.session.add(message)
                conversation.last_active_at = utc_now()
                await self.session.commit()
                response = ChatResponse(
                    conversation_uuid=conversation.id,
                    message_id=message.id,
                    answer=result.answer,
                    citations=result.citations,
                    tool_calls=result.tool_calls,
                    prompt_tokens=result.prompt_tokens,
                    completion_tokens=result.completion_tokens,
                    cost=float(cost),
                    latency_ms=latency_ms,
                    status=result.status,
                )
                yield {"type": "done", "data": response.model_dump(mode="json")}
        except Exception as error:
            await self.session.rollback()
            latency_ms = int((perf_counter() - started) * 1000)
            friendly = "小苏暂时无法连接模型服务，请稍后重试或联系管理员检查 API Key。"
            message = Message(
                id=uuid4(),
                conversation_id=conversation.id,
                role="assistant",
                content=friendly,
                status="failed",
                model=self.settings.llm_model,
                latency_ms=latency_ms,
                error_code=type(error).__name__,
            )
            self.session.add(message)
            await self.session.commit()
            response = ChatResponse(
                conversation_uuid=conversation.id,
                message_id=message.id,
                answer=friendly,
                citations=[],
                tool_calls=[],
                prompt_tokens=0,
                completion_tokens=0,
                cost=0,
                latency_ms=latency_ms,
                status="failed",
            )
            yield {"type": "delta", "content": friendly}
            yield {"type": "done", "data": response.model_dump(mode="json")}

    async def _conversation(self, request: ChatRequest) -> Conversation:
        statement = select(Conversation).where(
            Conversation.platform == request.platform,
            Conversation.tenant_id == request.tenant_id,
            Conversation.external_conversation_id == request.conversation_id,
            Conversation.external_user_id == request.user_id,
        )
        conversation = await self.session.scalar(statement)
        if conversation is None:
            conversation = Conversation(
                platform=request.platform,
                tenant_id=request.tenant_id,
                external_conversation_id=request.conversation_id,
                external_user_id=request.user_id,
                user_name=request.user_name,
                title=request.message[:80],
            )
            self.session.add(conversation)
            await self.session.flush()
        return conversation

    async def _history(self, conversation_id) -> list[dict[str, object]]:
        messages = await self.session.scalars(
            select(Message)
            .where(Message.conversation_id == conversation_id)
            .order_by(Message.created_at.desc())
            .limit(20)
        )
        ordered = reversed(list(messages))
        return [{"role": message.role, "content": message.content} for message in ordered]

    def _cost(self, prompt_tokens: int, completion_tokens: int) -> Decimal:
        value = (
            prompt_tokens * self.settings.input_price_per_million
            + completion_tokens * self.settings.output_price_per_million
        ) / 1_000_000
        return Decimal(str(round(value, 8)))
