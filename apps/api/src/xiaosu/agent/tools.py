from datetime import date, datetime
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pydantic import TypeAdapter
from sqlalchemy.ext.asyncio import AsyncSession

from xiaosu.core.config import Settings
from xiaosu.knowledge.schemas import Citation
from xiaosu.knowledge.service import DocumentService
from xiaosu.mock.service import InvalidDateRangeError, mock_internal_system

TOOL_DEFINITIONS: list[dict[str, object]] = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "检索公司制度、员工手册、流程、FAQ 和其他已上传文档。",
            "parameters": {
                "type": "object",
                "properties": {"query": {"type": "string", "description": "完整检索问题"}},
                "required": ["query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_employee",
            "description": "按三位员工编号查询姓名、部门、职级等信息。",
            "parameters": {
                "type": "object",
                "properties": {"employee_id": {"type": "string", "pattern": "^\\d{3}$"}},
                "required": ["employee_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_attendance",
            "description": "查询某员工在日期范围内的出勤、迟到、请假和加班情况。",
            "parameters": {
                "type": "object",
                "properties": {
                    "employee_id": {"type": "string"},
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["employee_id", "start_date", "end_date"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_orders",
            "description": "查询日期范围内订单，并返回订单数、销售额、退款和净销售额汇总。",
            "parameters": {
                "type": "object",
                "properties": {
                    "start_date": {"type": "string", "format": "date"},
                    "end_date": {"type": "string", "format": "date"},
                },
                "required": ["start_date", "end_date"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "查询当前日期和时间。",
            "parameters": {
                "type": "object",
                "properties": {
                    "timezone": {"type": "string", "description": "IANA 时区，默认 Asia/Shanghai"}
                },
                "additionalProperties": False,
            },
        },
    },
]


class AgentToolExecutor:
    def __init__(self, session: AsyncSession, settings: Settings) -> None:
        self._documents = DocumentService(session, settings)
        self._settings = settings
        self.citations: list[Citation] = []
        self.knowledge_search_attempted = False

    async def execute(self, name: str, arguments: dict[str, object]) -> dict[str, Any]:
        try:
            if name == "search_knowledge":
                self.knowledge_search_attempted = True
                query = str(arguments.get("query", ""))
                citations = await self._documents.search(query, self._settings.retrieval_top_k)
                citations = [
                    citation
                    for citation in citations
                    if citation.score >= self._settings.retrieval_min_score
                ]
                self.citations.extend(citations)
                return {
                    "found": bool(citations),
                    "matches": [citation.model_dump(mode="json") for citation in citations],
                }
            if name == "get_employee":
                employee = mock_internal_system.get_employee(str(arguments.get("employee_id", "")))
                return {"found": employee is not None, "employee": _dump(employee)}
            if name == "query_attendance":
                result = mock_internal_system.query_attendance(
                    str(arguments.get("employee_id", "")),
                    _date(arguments.get("start_date")),
                    _date(arguments.get("end_date")),
                )
                return _dump(result)
            if name == "query_orders":
                result = mock_internal_system.query_orders(
                    _date(arguments.get("start_date")),
                    _date(arguments.get("end_date")),
                )
                return _dump(result)
            if name == "get_current_time":
                timezone_name = str(arguments.get("timezone", "Asia/Shanghai"))
                try:
                    timezone = ZoneInfo(timezone_name)
                except ZoneInfoNotFoundError:
                    timezone_name = "Asia/Shanghai"
                    timezone = ZoneInfo(timezone_name)
                now = datetime.now(timezone)
                return {"timezone": timezone_name, "datetime": now.isoformat()}
            return {"error": f"未知工具：{name}"}
        except (ValueError, InvalidDateRangeError) as error:
            return {"error": str(error)}


def _date(value: object) -> date:
    return date.fromisoformat(str(value))


def _dump(value: object) -> Any:
    if value is None:
        return None
    return TypeAdapter(type(value)).dump_python(value, mode="json")
