import json
from functools import lru_cache
from pathlib import Path

from pydantic import TypeAdapter

from xiaosu.mock.models import AttendanceRecord, Employee, Order

DATA_DIRECTORY = Path(__file__).parent / "data"


def _read_json(filename: str) -> object:
    path = DATA_DIRECTORY / filename
    with path.open(encoding="utf-8") as file:
        return json.load(file)


@lru_cache
def load_employees() -> tuple[Employee, ...]:
    adapter = TypeAdapter(list[Employee])
    return tuple(adapter.validate_python(_read_json("employees.json")))


@lru_cache
def load_attendance() -> tuple[AttendanceRecord, ...]:
    adapter = TypeAdapter(list[AttendanceRecord])
    return tuple(adapter.validate_python(_read_json("attendance.json")))


@lru_cache
def load_orders() -> tuple[Order, ...]:
    adapter = TypeAdapter(list[Order])
    return tuple(adapter.validate_python(_read_json("orders.json")))
