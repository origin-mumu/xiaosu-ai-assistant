from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from xiaosu.core.config import Settings, get_settings
from xiaosu.main import app


def auth_settings() -> Settings:
    return Settings(
        admin_username="admin",
        admin_password=SecretStr("test-password"),
        session_secret=SecretStr("test-session-secret"),
    )


async def test_login_session_and_logout() -> None:
    app.dependency_overrides[get_settings] = auth_settings
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            unauthorized = await client.get("/api/v1/auth/me")
            assert unauthorized.status_code == 401

            login = await client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "test-password"},
            )
            assert login.status_code == 200
            assert login.json() == {"username": "admin"}
            assert login.cookies.get("xiaosu_session")

            current = await client.get("/api/v1/auth/me")
            assert current.status_code == 200
            assert current.json() == {"username": "admin"}

            logout = await client.post("/api/v1/auth/logout")
            assert logout.status_code == 204
            assert (await client.get("/api/v1/auth/me")).status_code == 401
    finally:
        app.dependency_overrides.clear()


async def test_login_rejects_wrong_password() -> None:
    app.dependency_overrides[get_settings] = auth_settings
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "wrong-password"},
            )
        assert response.status_code == 401
        assert response.json()["detail"] == "用户名或密码错误"
    finally:
        app.dependency_overrides.clear()
