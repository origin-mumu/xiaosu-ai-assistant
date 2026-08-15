from datetime import date
from decimal import Decimal

from xiaosu.mock.models import (
    AttendanceQueryResult,
    AttendanceStatus,
    AttendanceSummary,
    Employee,
    OrdersQueryResult,
    OrderStatus,
    OrderSummary,
)
from xiaosu.mock.repository import load_attendance, load_employees, load_orders


class InvalidDateRangeError(ValueError):
    """Raised when a query starts after it ends."""


class MockInternalSystemService:
    def get_employee(self, employee_id: str) -> Employee | None:
        return next(
            (employee for employee in load_employees() if employee.id == employee_id),
            None,
        )

    def find_employees(self, name: str) -> list[Employee]:
        normalized = name.strip().casefold()
        if not normalized:
            return []
        return [employee for employee in load_employees() if normalized in employee.name.casefold()]

    def query_attendance(
        self,
        employee_id: str,
        start_date: date,
        end_date: date,
    ) -> AttendanceQueryResult:
        self._validate_range(start_date, end_date)
        records = sorted(
            (
                record
                for record in load_attendance()
                if record.emp_id == employee_id and start_date <= record.date <= end_date
            ),
            key=lambda record: record.date,
        )
        present_statuses = {
            AttendanceStatus.NORMAL,
            AttendanceStatus.LATE,
            AttendanceStatus.OVERTIME,
            AttendanceStatus.MISSING_PUNCH,
        }
        summary = AttendanceSummary(
            scheduled_days=len(records),
            present_days=sum(record.status in present_statuses for record in records),
            late_days=sum(record.status == AttendanceStatus.LATE for record in records),
            leave_days=sum(record.status == AttendanceStatus.LEAVE for record in records),
            absent_days=sum(record.status == AttendanceStatus.ABSENT for record in records),
            overtime_days=sum(record.status == AttendanceStatus.OVERTIME for record in records),
            missing_punch_days=sum(
                record.status == AttendanceStatus.MISSING_PUNCH for record in records
            ),
        )
        return AttendanceQueryResult(
            employee_id=employee_id,
            start_date=start_date,
            end_date=end_date,
            records=records,
            summary=summary,
        )

    def query_orders(self, start_date: date, end_date: date) -> OrdersQueryResult:
        self._validate_range(start_date, end_date)
        records = sorted(
            (order for order in load_orders() if start_date <= order.date <= end_date),
            key=lambda order: (order.date, order.id),
        )
        effective_orders = [order for order in records if order.status != OrderStatus.CANCELLED]
        gross_amount = sum((order.amount for order in effective_orders), start=Decimal("0"))
        refund_amount = sum(
            (order.refund_amount for order in effective_orders),
            start=Decimal("0"),
        )
        summary = OrderSummary(
            order_count=len(effective_orders),
            cancelled_count=sum(order.status == OrderStatus.CANCELLED for order in records),
            gross_amount=gross_amount,
            refund_amount=refund_amount,
            net_amount=gross_amount - refund_amount,
        )
        return OrdersQueryResult(
            start_date=start_date,
            end_date=end_date,
            records=records,
            summary=summary,
        )

    @staticmethod
    def _validate_range(start_date: date, end_date: date) -> None:
        if start_date > end_date:
            raise InvalidDateRangeError("start_date must be on or before end_date")


mock_internal_system = MockInternalSystemService()
