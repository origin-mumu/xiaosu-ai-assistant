from uuid import uuid4

from dingtalk_stream import ChatbotMessage

from xiaosu.agent.sources import format_im_sources
from xiaosu.im.dingtalk import _absolute_links, to_chat_request
from xiaosu.knowledge.schemas import Citation


def test_dingtalk_identity_isolated_by_user_and_conversation() -> None:
    incoming = ChatbotMessage.from_dict(
        {
            "msgtype": "text",
            "text": {"content": " 员工 001 是哪个部门的？ "},
            "senderCorpId": "corp-1",
            "conversationId": "group-1",
            "senderStaffId": "user-1",
            "senderNick": "面试官",
        }
    )

    request = to_chat_request(incoming)

    assert request.message == "员工 001 是哪个部门的？"
    assert request.tenant_id == "corp-1"
    assert request.conversation_id == "group-1"
    assert request.user_id == "user-1"


def test_dingtalk_relative_citation_link_becomes_absolute() -> None:
    markdown = "[员工手册](/documents/doc-1?chunk=chunk-1)"
    assert _absolute_links(markdown, "https://demo.example.com") == (
        "[员工手册](https://demo.example.com/documents/doc-1?chunk=chunk-1)"
    )


def test_dingtalk_answer_lists_document_and_tool_sources() -> None:
    document_id = uuid4()
    chunk_id = uuid4()
    markdown = format_im_sources(
        [
            Citation(
                chunk_id=chunk_id,
                document_id=document_id,
                filename="员工手册.md",
                section_title="考勤制度",
                content="员工应在上班前完成打卡。",
                score=0.9,
            )
        ],
        [
            {
                "name": "get_employee",
                "arguments": {"employee_id": "001"},
                "result": {"found": True},
            }
        ],
        "https://demo.example.com",
    )

    assert "引用与数据来源" in markdown
    assert f"https://demo.example.com/documents/{document_id}?chunk={chunk_id}" in markdown
    assert "员工信息查询" in markdown
    assert "get_employee" not in markdown
    assert "employee_id" not in markdown
