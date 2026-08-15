import json
from collections.abc import Sequence
from typing import Protocol

from openai import AsyncOpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

from xiaosu.agent.schemas import AgentToolCall, ModelTurn
from xiaosu.core.config import Settings
from xiaosu.knowledge.embeddings import ModelConfigurationError


class ChatModel(Protocol):
    async def complete(
        self,
        messages: Sequence[dict[str, object]],
        tools: Sequence[dict[str, object]],
    ) -> ModelTurn: ...


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
