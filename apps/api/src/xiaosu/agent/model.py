import json
from collections.abc import AsyncIterator, Sequence
from typing import Protocol

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from xiaosu.agent.schemas import AgentToolCall, ModelStreamEvent, ModelTurn
from xiaosu.core.config import Settings
from xiaosu.knowledge.embeddings import ModelConfigurationError


class ChatModel(Protocol):
    async def complete(
        self,
        messages: Sequence[dict[str, object]],
        tools: Sequence[dict[str, object]],
    ) -> ModelTurn: ...

    def stream(
        self,
        messages: Sequence[dict[str, object]],
        tools: Sequence[dict[str, object]],
    ) -> AsyncIterator[ModelStreamEvent]: ...


class DashScopeChatModel:
    def __init__(self, settings: Settings) -> None:
        secret = settings.dashscope_api_key
        if secret is None or not secret.get_secret_value():
            raise ModelConfigurationError("请先在本机 .env 填写 DASHSCOPE_API_KEY")
        self._model = settings.llm_model
        self._client = AsyncOpenAI(
            api_key=secret.get_secret_value(),
            base_url=settings.dashscope_base_url,
            timeout=settings.model_timeout_seconds,
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def complete(
        self,
        messages: Sequence[dict[str, object]],
        tools: Sequence[dict[str, object]],
    ) -> ModelTurn:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=list(messages),  # type: ignore[arg-type]
            tools=list(tools),  # type: ignore[arg-type]
            tool_choice="auto",
            temperature=0.1,
        )
        choice = response.choices[0].message
        calls: list[AgentToolCall] = []
        for call in choice.tool_calls or []:
            try:
                arguments = json.loads(call.function.arguments)
            except json.JSONDecodeError:
                arguments = {}
            calls.append(AgentToolCall(call.id, call.function.name, arguments))
        usage = response.usage
        return ModelTurn(
            content=choice.content or "",
            tool_calls=calls,
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
        )

    async def stream(
        self,
        messages: Sequence[dict[str, object]],
        tools: Sequence[dict[str, object]],
    ) -> AsyncIterator[ModelStreamEvent]:
        response = await self._create_stream(messages, tools)
        content_parts: list[str] = []
        calls: dict[int, dict[str, str]] = {}
        prompt_tokens = 0
        completion_tokens = 0
        async for chunk in response:
            usage = chunk.usage
            if usage:
                prompt_tokens = usage.prompt_tokens
                completion_tokens = usage.completion_tokens
            if not chunk.choices:
                continue
            delta = chunk.choices[0].delta
            if delta.content:
                content_parts.append(delta.content)
                yield ModelStreamEvent(type="content", content=delta.content)
            for call in delta.tool_calls or []:
                item = calls.setdefault(call.index, {"id": "", "name": "", "arguments": ""})
                if call.id:
                    item["id"] = call.id
                if call.function:
                    if call.function.name:
                        item["name"] += call.function.name
                    if call.function.arguments:
                        item["arguments"] += call.function.arguments

        tool_calls: list[AgentToolCall] = []
        for index, call in sorted(calls.items()):
            try:
                arguments = json.loads(call["arguments"] or "{}")
            except json.JSONDecodeError:
                arguments = {}
            tool_calls.append(AgentToolCall(call["id"] or f"tool-{index}", call["name"], arguments))
        yield ModelStreamEvent(
            type="done",
            turn=ModelTurn(
                content="".join(content_parts),
                tool_calls=tool_calls,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
            ),
        )

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(min=1, max=8), reraise=True)
    async def _create_stream(
        self,
        messages: Sequence[dict[str, object]],
        tools: Sequence[dict[str, object]],
    ):
        return await self._client.chat.completions.create(
            model=self._model,
            messages=list(messages),  # type: ignore[arg-type]
            tools=list(tools),  # type: ignore[arg-type]
            tool_choice="auto",
            temperature=0.1,
            stream=True,
            stream_options={"include_usage": True},
        )
