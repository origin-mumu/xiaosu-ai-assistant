from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from httpx import ASGITransport, AsyncClient
from pydantic import SecretStr

from xiaosu.core.config import Settings, get_settings
from xiaosu.main import app


@asynccontextmanager
async def authenticated_client() -> AsyncIterator[AsyncClient]:
    settings = Settings(
        admin_username="admin",
        admin_password=SecretStr("test-password"),
        session_secret=SecretStr("test-session-secret"),
    )
    app.dependency_overrides[get_settings] = lambda: settings
    transport = ASGITransport(app=app)
    try:
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            login = await client.post(
                "/api/v1/auth/login",
                json={"username": "admin", "password": "test-password"},
            )
            assert login.status_code == 200
            yield client
    finally:
        app.dependency_overrides.clear()


async def test_get_employee_returns_expected_department() -> None:
    async with authenticated_client() as client:
        response = await client.get("/api/v1/mock/employees/001")

    assert response.status_code == 200
    assert response.json() == {
        "id": "001",
        "name": "张三",
        "dept": "研发部",
        "level": "P5",
        "status": "active",
    }


async def test_find_employee_by_name_supports_follow_up_tool_calls() -> None:
    async with authenticated_client() as client:
        response = await client.get("/api/v1/mock/employees", params={"name": "张三"})

    assert response.status_code == 200
    assert response.json()[0]["id"] == "001"


async def test_get_unknown_employee_returns_404() -> None:
    async with authenticated_client() as client:
        response = await client.get("/api/v1/mock/employees/999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Employee not found"


async def test_attendance_summary_covers_leave_late_and_overtime() -> None:
    params = {
        "employee_id": "001",
        "start_date": "2026-08-03",
        "end_date": "2026-08-09",
    }
    async with authenticated_client() as client:
        response = await client.get("/api/v1/mock/attendance", params=params)

    assert response.status_code == 200
    assert response.json()["summary"] == {
        "scheduled_days": 5,
        "present_days": 4,
        "late_days": 1,
        "leave_days": 1,
        "absent_days": 0,
        "overtime_days": 1,
        "missing_punch_days": 0,
    }


async def test_order_summary_excludes_cancelled_and_subtracts_refunds() -> None:
    params = {
        "start_date": "2026-08-03",
        "end_date": "2026-08-09",
    }
    async with authenticated_client() as client:
        response = await client.get("/api/v1/mock/orders", params=params)

    assert response.status_code == 200
    assert response.json()["summary"] == {
        "order_count": 7,
        "cancelled_count": 1,
        "gross_amount": "14399.00",
        "refund_amount": "1560.00",
        "net_amount": "12839.00",
    }


async def test_invalid_date_range_returns_422() -> None:
    params = {
        "start_date": "2026-08-10",
        "end_date": "2026-08-03",
    }
    async with authenticated_client() as client:
        response = await client.get("/api/v1/mock/orders", params=params)

    assert response.status_code == 422
    assert response.json()["detail"] == "start_date must be on or before end_date"
