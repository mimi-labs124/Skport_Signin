from __future__ import annotations

from dataclasses import dataclass

from efcheck.statuses import ALREADY_DONE, READY_TO_SIGN, UNKNOWN


@dataclass
class AttendanceState:
    status: str
    day_number: int | None = None
    available_count: int = 0


def derive_attendance_state(payload: dict) -> AttendanceState:
    calendar = payload.get("data", {}).get("calendar", [])
    if not calendar:
        return AttendanceState(status=UNKNOWN, day_number=None, available_count=0)
    available_indexes = [
        index + 1
        for index, item in enumerate(calendar)
        if item.get("available") and not item.get("done")
    ]
    if available_indexes:
        return AttendanceState(
            status=READY_TO_SIGN,
            day_number=available_indexes[0],
            available_count=len(available_indexes),
        )
    return AttendanceState(status=ALREADY_DONE, day_number=None, available_count=0)
