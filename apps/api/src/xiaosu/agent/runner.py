import json
from collections.abc import AsyncIterator, Sequence
from datetime import datetime
from time import perf_counter
from zoneinfo import ZoneInfo

from xiaosu.agent.model import ChatModel
from xiaosu.agent.prompts import system_prompt
from xiaosu.agent.schemas import AgentResult, AgentStreamEvent, ModelTurn
from xiaosu.agent.sources import tool_display_name
from xiaosu.agent.tools import AgentToolExecutor, TOOL_DEFINITIONS


class AgentRunner:
    def __init__(
        self,
        model: ChatModel,
        tools: AgentToolExecutor,
        max_steps: int = 5,
    ) -> None:
        self.model = model
        self.tools = tools
        self.max_steps = max_steps

    async def run(
        self,
        history: Sequence[dict[str, object]],
        user_message: str,
    ) -> AgentResult:
        messages: list[dict[str, object]] = [
            {"role": "system", "content": system_prompt(datetime.now(ZoneInfo("Asia/Shanghai")))},
            *history,
            {"role": "user", "content": user_message},
        ]
        call_logs: list[dict[str, object]] = []
        prompt_tokens = 0
        completion_tokens = 0
        answer = "抱歉，我暂时无法完成这个请求。"

        for _ in range(self.max_steps):
            turn = await self.model.complete(messages, TOOL_DEFINITIONS)
            prompt_tokens += turn.prompt_tokens
            completion_tokens += turn.completion_tokens
            if not turn.tool_calls:
                answer = turn.content.strip() or answer
                break

            messages.append(
                {
                    "role": "assistant",
                    "content": turn.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.name,
                                "arguments": json.dumps(call.arguments, ensure_ascii=False),
                            },
                        }
                        for call in turn.tool_calls
                    ],
                }
            )
            for call in turn.tool_calls:
                result, log = await self._execute_tool(call.name, call.arguments)
                call_logs.append(log)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        result_status = "completed"
        if self.tools.knowledge_search_attempted and not self.tools.citations:
            answer = "文档里没找到相关信息，我不能根据猜测作答。你可以联系管理员补充知识库。"
            result_status = "unanswered"
        return AgentResult(
            answer=answer,
            citations=self.tools.citations,
            tool_calls=call_logs,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            status=result_status,
        )

    async def stream(
        self,
        history: Sequence[dict[str, object]],
        user_message: str,
    ) -> AsyncIterator[AgentStreamEvent]:
        messages: list[dict[str, object]] = [
            {"role": "system", "content": system_prompt(datetime.now(ZoneInfo("Asia/Shanghai")))},
            *history,
            {"role": "user", "content": user_message},
        ]
        call_logs: list[dict[str, object]] = []
        prompt_tokens = 0
        completion_tokens = 0
        answer_parts: list[str] = []
        answer = "抱歉，我暂时无法完成这个请求。"

        yield AgentStreamEvent(
            type="status",
            stage="understanding",
            label="理解用户问题",
            detail="分析意图、上下文与需要的数据来源",
            phase="start",
        )
        for step in range(self.max_steps):
            turn: ModelTurn | None = None
            step_deltas: list[str] = []
            async for event in self.model.stream(messages, TOOL_DEFINITIONS):
                if event.type == "content" and event.content:
                    step_deltas.append(event.content)
                elif event.type == "done":
                    turn = event.turn
            if turn is None:
                raise RuntimeError("模型流未返回完成事件")
            prompt_tokens += turn.prompt_tokens
            completion_tokens += turn.completion_tokens

            if not turn.tool_calls:
                # 最终作答轮次：流式推送回答
                yield AgentStreamEvent(
                    type="status",
                    stage="generating",
                    label="组织最终答案",
                    detail="结合工具返回结果生成回复",
                    phase="start",
                )
                for chunk in step_deltas:
                    answer_parts.append(chunk)
                    yield AgentStreamEvent(type="delta", content=chunk)
                answer = "".join(step_deltas).strip() or turn.content.strip() or answer
                break

            # 触发了工具调用
            messages.append(
                {
                    "role": "assistant",
                    "content": turn.content,
                    "tool_calls": [
                        {
                            "id": call.id,
                            "type": "function",
                            "function": {
                                "name": call.name,
                                "arguments": json.dumps(call.arguments, ensure_ascii=False),
                            },
                        }
                        for call in turn.tool_calls
                    ],
                }
            )
            for call in turn.tool_calls:
                display_name = tool_display_name(call.name)
                stage = f"tool:{call.id}"
                yield AgentStreamEvent(
                    type="status",
                    stage=stage,
                    label=f"调用工具：{display_name}",
                    detail="正在连接内部系统并查询所需数据",
                    phase="start",
                    tool_name=call.name,
                    arguments=call.arguments,
                )
                result, log = await self._execute_tool(call.name, call.arguments)
                call_logs.append(log)
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )
                yield AgentStreamEvent(
                    type="status",
                    stage=stage,
                    label=f"工具完成：{display_name}",
                    detail=_result_summary(result),
                    phase="complete",
                    tool_name=call.name,
                    arguments=call.arguments,
                    tool_result=result,
                )

            if self.tools.knowledge_search_attempted and not self.tools.citations:
                answer = "文档里没找到相关信息，我不能根据猜测作答。你可以联系管理员补充知识库。"
                answer_parts = [answer]
                yield AgentStreamEvent(
                    type="status",
                    stage="generating",
                    label="组织最终答案",
                    detail="未检索到有效信息，执行安全拒答",
                    phase="start",
                )
                yield AgentStreamEvent(type="delta", content=answer)
                break

        answer = "".join(answer_parts).strip() or answer
        result_status = (
            "unanswered"
            if self.tools.knowledge_search_attempted and not self.tools.citations
            else "completed"
        )
        yield AgentStreamEvent(
            type="done",
            result=AgentResult(
                answer=answer,
                citations=self.tools.citations,
                tool_calls=call_logs,
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                status=result_status,
            ),
        )

    async def _execute_tool(
        self,
        name: str,
        arguments: dict[str, object],
    ) -> tuple[dict[str, object], dict[str, object]]:
        started = perf_counter()
        result = await self.tools.execute(name, arguments)
        duration_ms = int((perf_counter() - started) * 1000)
        success = "error" not in result
        return result, {
            "name": name,
            "arguments": arguments,
            "result": result,
            "duration_ms": duration_ms,
            "success": success,
        }


def _json_preview(value: object, limit: int = 120) -> str:
    text = json.dumps(value, ensure_ascii=False, separators=(", ", ": "))
    return text if len(text) <= limit else f"{text[:limit]}…"


def _result_summary(result: dict[str, object]) -> str:
    if "error" in result:
        return f"调用失败：{result['error']}"
    if "found" in result:
        return "已找到匹配数据" if result["found"] else "未找到匹配数据"
    return f"已返回结果：{_json_preview(result)}"
