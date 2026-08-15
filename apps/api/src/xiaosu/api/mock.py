from datetime import date
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from xiaosu.api.auth import require_admin
from xiaosu.mock.models import AttendanceQueryResult, Employee, OrdersQueryResult
from xiaosu.mock.service import InvalidDateRangeError, mock_internal_system

router = APIRouter(
    prefix="/mock",
    tags=["mock internal systems"],
    dependencies=[Depends(require_admin)],
)


@router.get("/employees/{employee_id}", response_model=Employee)
async def get_employee(employee_id: str) -> Employee:
    employee = mock_internal_system.get_employee(employee_id)
    if employee is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    return employee


@router.get("/attendance", response_model=AttendanceQueryResult)
async def query_attendance(
    employee_id: Annotated[str, Query(pattern=r"^\d{3}$")],
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
) -> AttendanceQueryResult:
    if mock_internal_system.get_employee(employee_id) is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Employee not found",
        )
    try:
        return mock_internal_system.query_attendance(employee_id, start_date, end_date)
    except InvalidDateRangeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error


@router.get("/orders", response_model=OrdersQueryResult)
async def query_orders(
    start_date: Annotated[date, Query()],
    end_date: Annotated[date, Query()],
) -> OrdersQueryResult:
    try:
        return mock_internal_system.query_orders(start_date, end_date)
    except InvalidDateRangeError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(error),
        ) from error
