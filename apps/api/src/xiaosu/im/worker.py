import logging
import sys
from threading import Event, Thread

from dingtalk_stream import ChatbotMessage, Credential, DingTalkStreamClient

from xiaosu.core.config import get_settings
from xiaosu.core.logging import setup_logging
from xiaosu.im.dingtalk import XiaosuDingTalkHandler
from xiaosu.im.status import write_heartbeat

logger = logging.getLogger(__name__)


def main() -> int:
    settings = get_settings()
    setup_logging(settings.log_dir)
    client_id = settings.dingtalk_client_id
    client_secret = settings.dingtalk_client_secret
    if not client_id or not client_id.get_secret_value():
        logger.error("DINGTALK_CLIENT_ID is not configured")
        return 2
    if not client_secret or not client_secret.get_secret_value():
        logger.error("DINGTALK_CLIENT_SECRET is not configured")
        return 2

    credential = Credential(client_id.get_secret_value(), client_secret.get_secret_value())
    client = DingTalkStreamClient(credential)
    client.register_callback_handler(
        ChatbotMessage.TOPIC,
        XiaosuDingTalkHandler(settings),
    )
    stop_event = Event()
    heartbeat = Thread(
        target=write_heartbeat,
        args=(settings.log_dir, stop_event),
        name="dingtalk-heartbeat",
        daemon=True,
    )
    heartbeat.start()
    logger.info("Starting DingTalk Stream client")
    try:
        client.start_forever()
    finally:
        stop_event.set()
        heartbeat.join(timeout=2)
    return 0


if __name__ == "__main__":
    sys.exit(main())
