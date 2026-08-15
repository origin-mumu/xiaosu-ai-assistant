from datetime import date, time
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator


class EmploymentStatus(StrEnum):
    ACTIVE = "active"
    LEAVE = "leave"
    TERMINATED = "terminated"


class Employee(BaseModel):
    id: str = Field(pattern=r"^\d{3}$")
    name: str = Field(min_length=1, max_length=50)
    dept: str = Field(min_length=1, max_length=100)
    level: str = Field(min_length=1, max_length=20)
    status: EmploymentStatus


class AttendanceStatus(StrEnum):
    NORMAL = "normal"
    LATE = "late"
    LEAVE = "leave"
    ABSENT = "absent"
    OVERTIME = "overtime"
    MISSING_PUNCH = "missing_punch"


class AttendanceRecord(BaseModel):
    emp_id: str = Field(pattern=r"^\d{3}$")
    date: date
    check_in: time | None = None
    check_out: time | None = None
    status: AttendanceStatus


class AttendanceSummary(BaseModel):
    scheduled_days: int = Field(ge=0)
    present_days: int = Field(ge=0)
    late_days: int = Field(ge=0)
    leave_days: int = Field(ge=0)
    absent_days: int = Field(ge=0)
    overtime_days: int = Field(ge=0)
    missing_punch_days: int = Field(ge=0)


class AttendanceQueryResult(BaseModel):
    employee_id: str
    start_date: date
    end_date: date
    records: list[AttendanceRecord]
    summary: AttendanceSummary


class OrderStatus(StrEnum):
    PAID = "paid"
    PARTIAL_REFUND = "partial_refund"
    REFUNDED = "refunded"
    CANCELLED = "cancelled"


class Order(BaseModel):
    id: str = Field(min_length=1, max_length=32)
    amount: Decimal = Field(ge=0)
    refund_amount: Decimal = Field(default=Decimal("0"), ge=0)
    date: date
    customer: str = Field(min_length=1, max_length=100)
    status: OrderStatus

    @model_validator(mode="after")
    def refund_must_not_exceed_amount(self) -> "Order":
        if self.refund_amount > self.amount:
            raise ValueError("refund_amount must not exceed amount")
        return self


class OrderSummary(BaseModel):
    order_count: int = Field(ge=0)
    cancelled_count: int = Field(ge=0)
    gross_amount: Decimal = Field(ge=0)
    refund_amount: Decimal = Field(ge=0)
    net_amount: Decimal = Field(ge=0)


class OrdersQueryResult(BaseModel):
    start_date: date
    end_date: date
    records: list[Order]
    summary: OrderSummary
