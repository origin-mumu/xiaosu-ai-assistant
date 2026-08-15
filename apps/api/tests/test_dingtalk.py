from dingtalk_stream import ChatbotMessage

from xiaosu.im.dingtalk import _absolute_links, to_chat_request


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
