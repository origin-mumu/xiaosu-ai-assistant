import json
from collections.abc import Sequence
from datetime import datetime
from zoneinfo import ZoneInfo

from xiaosu.agent.model import ChatModel
from xiaosu.agent.prompts import system_prompt
from xiaosu.agent.schemas import AgentResult
from xiaosu.agent.tools import TOOL_DEFINITIONS, AgentToolExecutor


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
                result = await self.tools.execute(call.name, call.arguments)
                call_logs.append({"name": call.name, "arguments": call.arguments, "result": result})
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": call.id,
                        "content": json.dumps(result, ensure_ascii=False),
                    }
                )

        if self.tools.knowledge_search_attempted and not self.tools.citations:
            answer = "文档里没找到相关信息，我不能根据猜测作答。你可以联系管理员补充知识库。"
        elif self.tools.citations:
            answer = f"{answer}\n\n{_citation_markdown(self.tools.citations)}"
        return AgentResult(
            answer=answer,
            citations=self.tools.citations,
            tool_calls=call_logs,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
        )


def _citation_markdown(citations: list) -> str:
    lines = ["**参考来源**"]
    for index, citation in enumerate(citations, start=1):
        location = []
        if citation.section_title:
            location.append(citation.section_title)
        if citation.page_number:
            location.append(f"第 {citation.page_number} 页")
        if citation.paragraph_start:
            location.append(f"第 {citation.paragraph_start} 段")
        label = " · ".join(location) or "原文片段"
        lines.append(
            f"{index}. [{citation.filename} · {label}]"
            f"(/documents/{citation.document_id}?chunk={citation.chunk_id})"
        )
    return "\n".join(lines)
