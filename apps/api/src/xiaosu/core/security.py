import base64
import hashlib
import hmac
import json
import time

from xiaosu.core.config import Settings

SESSION_COOKIE = "xiaosu_session"


def auth_is_configured(settings: Settings) -> bool:
    return bool(_password(settings) and _signing_secret(settings))


def authenticate_admin(username: str, password: str, settings: Settings) -> bool:
    expected_password = _password(settings)
    if not expected_password:
        return False
    return hmac.compare_digest(username, settings.admin_username) and hmac.compare_digest(
        password,
        expected_password,
    )


def create_session_token(settings: Settings) -> str:
    secret = _signing_secret(settings)
    if not secret:
        raise ValueError("后台登录凭证尚未配置")
    payload = {
        "sub": settings.admin_username,
        "exp": int(time.time()) + settings.session_ttl_seconds,
    }
    encoded = _encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign(encoded, secret)
    return f"{encoded}.{signature}"


def validate_session_token(token: str, settings: Settings) -> str | None:
    secret = _signing_secret(settings)
    if not secret:
        return None
    try:
        encoded, supplied_signature = token.split(".", maxsplit=1)
        expected_signature = _sign(encoded, secret)
        if not hmac.compare_digest(supplied_signature, expected_signature):
            return None
        payload = json.loads(_decode(encoded))
        username = str(payload["sub"])
        expires_at = int(payload["exp"])
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None
    if expires_at <= int(time.time()) or username != settings.admin_username:
        return None
    return username


def _password(settings: Settings) -> str:
    value = settings.admin_password or settings.admin_token
    return value.get_secret_value() if value else "admin1500"


def _signing_secret(settings: Settings) -> str:
    value = settings.session_secret or settings.admin_token
    return value.get_secret_value() if value else ""


def _sign(encoded: str, secret: str) -> str:
    digest = hmac.new(secret.encode("utf-8"), encoded.encode("ascii"), hashlib.sha256).digest()
    return _encode(digest)


def _encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _decode(value: str) -> str:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode(value + padding).decode("utf-8")
