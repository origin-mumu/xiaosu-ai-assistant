from xiaosu.knowledge.schemas import Citation

TOOL_DISPLAY_NAMES = {
    "search_knowledge": "知识库检索",
    "find_employee": "员工姓名查询",
    "get_employee": "员工信息查询",
    "query_attendance": "考勤记录查询",
    "query_orders": "订单数据汇总",
    "get_current_time": "当前时间查询",
}


def tool_display_name(name: str) -> str:
    return TOOL_DISPLAY_NAMES.get(name, "内部工具")


def format_im_sources(
    citations: list[Citation],
    tool_calls: list[dict[str, object]],
    base_url: str | None = None,
) -> str:
    # 知识库检索的结果已通过具体文档引用 (citations) 展示，过滤掉冗余的 search_knowledge 工具名
    other_tools = [
        call for call in tool_calls
        if str(call.get("name", "")) != "search_knowledge"
    ]
    if not citations and not other_tools:
        return ""

    origin = (base_url or "").rstrip("/") or "http://localhost:8080"
    lines = ["---", "### 引用与数据来源"]
    for index, citation in enumerate(citations, start=1):
        location = []
        if citation.section_title:
            location.append(citation.section_title)
        if citation.page_number:
            location.append(f"第 {citation.page_number} 页")
        if citation.paragraph_start:
            location.append(f"第 {citation.paragraph_start} 段")
        label = " · ".join(location) or "原文片段"
        url = f"{origin}/documents/{citation.document_id}?chunk={citation.chunk_id}"
        lines.append(f"{index}. [📄 {citation.filename} · {label}]({url})")
        excerpt = " ".join(citation.content.split())
        if len(excerpt) > 160:
            excerpt = f"{excerpt[:160]}…"
        lines.append(f"   > {excerpt}")

    offset = len(citations)
    for index, call in enumerate(other_tools, start=1):
        name = str(call.get("name", "unknown"))
        lines.append(f"{offset + index}. 🔧 内部系统 · {tool_display_name(name)}")
    return "
".join(lines)
