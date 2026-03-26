from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
import json


@dataclass
class RunGateState:
    last_attempt_date: str | None = None
    last_status: str | None = None
    attempts_today: int = 0
    updated_at: str | None = None


def should_run_today(
    state_path: Path,
    today: str,
    *,
    max_attempts_per_day: int = 1,
) -> tuple[bool, RunGateState]:
    state = load_state(state_path)
    if state.last_attempt_date != today:
        return True, state
    if state.last_status in {"SUCCESS", "ALREADY_DONE"}:
        return False, state
    return state.attempts_today < max_attempts_per_day, state


def load_state(state_path: Path) -> RunGateState:
    if not state_path.exists():
        return RunGateState()

    data = json.loads(state_path.read_text(encoding="utf-8"))
    attempts_today = data.get("attempts_today")
    if attempts_today is None and data.get("last_attempt_date") and data.get("last_status"):
        attempts_today = 1
    return RunGateState(
        last_attempt_date=data.get("last_attempt_date"),
        last_status=data.get("last_status"),
        attempts_today=int(attempts_today or 0),
        updated_at=data.get("updated_at"),
    )


def mark_attempt(state_path: Path, state: RunGateState) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    state_path.write_text(
        json.dumps(asdict(state), ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
