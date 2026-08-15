from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Response, status
from pydantic import BaseModel, Field

from xiaosu.core.config import Settings, get_settings
from xiaosu.core.security import (
    SESSION_COOKIE,
    auth_is_configured,
    authenticate_admin,
    create_session_token,
    validate_session_token,
)

router = APIRouter(prefix="/auth", tags=["auth"])
SettingsDependency = Annotated[Settings, Depends(get_settings)]


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=1, max_length=200)


class AdminSessionResponse(BaseModel):
    username: str


def require_admin(
    settings: SettingsDependency,
    session_token: Annotated[str | None, Cookie(alias=SESSION_COOKIE)] = None,
) -> str:
    username = validate_session_token(session_token or "", settings)
    if username is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="登录状态已失效，请重新登录",
        )
    return username


@router.post("/login", response_model=AdminSessionResponse)
async def login(
    request: LoginRequest,
    response: Response,
    settings: SettingsDependency,
) -> AdminSessionResponse:
    if not auth_is_configured(settings):
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="管理员登录尚未配置，请检查本机 .env",
        )
    if not authenticate_admin(request.username, request.password, settings):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
        )
    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session_token(settings),
        max_age=settings.session_ttl_seconds,
        httponly=True,
        secure=settings.app_env == "production",
        samesite="strict",
        path="/",
    )
    return AdminSessionResponse(username=settings.admin_username)


@router.get("/me", response_model=AdminSessionResponse)
async def current_admin(
    username: Annotated[str, Depends(require_admin)],
) -> AdminSessionResponse:
    return AdminSessionResponse(username=username)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(response: Response) -> None:
    response.delete_cookie(SESSION_COOKIE, path="/", samesite="strict")
