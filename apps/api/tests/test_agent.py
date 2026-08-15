from xiaosu.agent.runner import AgentRunner
from xiaosu.agent.schemas import AgentToolCall, ModelStreamEvent, ModelTurn
from xiaosu.knowledge.schemas import Citation


class MockToolCallingModel:
    def __init__(self) -> None:
        self.calls = 0

    async def complete(self, messages, tools) -> ModelTurn:
        self.calls += 1
        if self.calls == 1:
            return ModelTurn(
                tool_calls=[AgentToolCall("call-1", "get_employee", {"employee_id": "001"})],
                prompt_tokens=10,
                completion_tokens=2,
            )
        assert messages[-1]["role"] == "tool"
        return ModelTurn(content="员工 001 在研发部。", prompt_tokens=12, completion_tokens=8)


class FakeTools:
    citations: list[Citation] = []
    knowledge_search_attempted = False

    async def execute(self, name, arguments):
        return {"found": True, "employee": {"id": "001", "department": "研发部"}}


async def test_mock_llm_autonomously_calls_employee_tool() -> None:
    model = MockToolCallingModel()
    result = await AgentRunner(model, FakeTools()).run([], "员工 001 是哪个部门的？")

    assert result.answer == "员工 001 在研发部。"
    assert result.tool_calls[0]["name"] == "get_employee"
    assert result.prompt_tokens == 22
    assert model.calls == 2


class HallucinatingModel:
    async def complete(self, messages, tools) -> ModelTurn:
        if messages[-1]["role"] == "user":
            return ModelTurn(
                tool_calls=[AgentToolCall("call-2", "search_knowledge", {"query": "CEO 地址"})]
            )
        return ModelTurn(content="CEO 住在某某路。")


class EmptyKnowledgeTools(FakeTools):
    knowledge_search_attempted = False

    async def execute(self, name, arguments):
        self.knowledge_search_attempted = True
        return {"found": False, "matches": []}


async def test_empty_knowledge_overrides_model_hallucination() -> None:
    tools = EmptyKnowledgeTools()
    result = await AgentRunner(HallucinatingModel(), tools).run([], "CEO 家庭住址是？")

    assert result.answer.startswith("文档里没找到相关信息")
    assert "某某路" not in result.answer
    assert result.status == "unanswered"


class StreamingToolCallingModel:
    def __init__(self) -> None:
        self.calls = 0

    async def stream(self, messages, tools):
        self.calls += 1
        if self.calls == 1:
            yield ModelStreamEvent(
                type="done",
                turn=ModelTurn(
                    tool_calls=[
                        AgentToolCall("call-stream", "get_employee", {"employee_id": "001"})
                    ],
                    prompt_tokens=5,
                    completion_tokens=1,
                ),
            )
            return
        yield ModelStreamEvent(type="content", content="员工 001 ")
        yield ModelStreamEvent(type="content", content="属于研发部。")
        yield ModelStreamEvent(
            type="done",
            turn=ModelTurn(
                content="员工 001 属于研发部。",
                prompt_tokens=7,
                completion_tokens=4,
            ),
        )


async def test_agent_streams_native_model_deltas_and_auditable_statuses() -> None:
    events = [
        event
        async for event in AgentRunner(StreamingToolCallingModel(), FakeTools()).stream(
            [], "员工 001 是哪个部门的？"
        )
    ]

    assert "".join(event.content for event in events if event.type == "delta") == (
        "员工 001 属于研发部。"
    )
    assert any(event.stage == "tool" and "员工" in (event.label or "") for event in events)
    result = events[-1].result
    assert result is not None
    assert result.tool_calls[0]["name"] == "get_employee"
    assert result.prompt_tokens == 12
