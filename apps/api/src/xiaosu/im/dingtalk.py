import asyncio
import logging

from dingtalk_stream import AckMessage, CallbackMessage, ChatbotHandler, ChatbotMessage

from xiaosu.agent.schemas import ChatRequest
from xiaosu.agent.service import ChatService
from xiaosu.agent.sources import format_im_sources
from xiaosu.core.config import Settings
from xiaosu.db.session import session_factory

logger = logging.getLogger(__name__)


def to_chat_request(incoming: ChatbotMessage) -> ChatRequest:
    text_parts = incoming.get_text_list() or []
    message = "\n".join(part.strip() for part in text_parts if part.strip())
    return ChatRequest(
        message=message or "（收到一条暂不支持的非文本消息）",
        platform="dingtalk",
        tenant_id=incoming.sender_corp_id or incoming.chatbot_corp_id or "default",
        conversation_id=incoming.conversation_id or "private",
        user_id=incoming.sender_staff_id or incoming.sender_id or "anonymous",
        user_name=incoming.sender_nick,
    )


class XiaosuDingTalkHandler(ChatbotHandler):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings

    async def process(self, callback: CallbackMessage) -> tuple[int, str]:
        try:
            incoming = ChatbotMessage.from_dict(callback.data)
            request = to_chat_request(incoming)
            async with session_factory() as session:
                result = await ChatService(session, self.settings).chat(request)
            sources = format_im_sources(
                result.citations,
                result.tool_calls,
                self.settings.public_base_url or self.settings.web_origin,
            )
            markdown = result.answer if not sources else f"{result.answer}\n\n{sources}"
            await asyncio.to_thread(
                self.reply_markdown,
                "小苏企业智能助手",
                markdown,
                incoming,
            )
            return AckMessage.STATUS_OK, "OK"
        except Exception:
            logger.exception("Failed to handle DingTalk message")
            try:
                incoming = ChatbotMessage.from_dict(callback.data)
                await asyncio.to_thread(
                    self.reply_text,
                    "小苏暂时开小差了，请稍后重试或联系管理员。",
                    incoming,
                )
            except Exception:
                logger.exception("Failed to send DingTalk fallback message")
            return AckMessage.STATUS_OK, "fallback sent"


def _absolute_links(markdown: str, base_url: str) -> str:
    """Keep compatibility for previously stored answers containing relative source links."""
    return markdown.replace("](/documents/", f"]({base_url.rstrip('/')}/documents/")
