from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from efcheck.errors import StateFileError


@dataclass
class RunGateState:
    last_attempt_date: str | None = None
    last_status: str | None = None
    updated_at: str | None = None


def should_run_today(state_path: Path, today: str) -> tuple[bool, RunGateState]:
    state = load_state(state_path)
    if state.last_attempt_date != today:
        return True, state
    if state.last_status in {"SUCCESS", "ALREADY_DONE"}:
        return False, state
    return True, state


def load_state(state_path: Path) -> RunGateState:
    if not state_path.exists():
        return RunGateState()

    try:
        data = json.loads(state_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise StateFileError(f"Could not parse state file at {state_path}: {exc.msg}.") from exc

    if not isinstance(data, dict):
        raise StateFileError(
            f"State file at {state_path} must contain a JSON object, not {type(data).__name__}."
        )

    return RunGateState(
        last_attempt_date=data.get("last_attempt_date"),
        last_status=data.get("last_status"),
        updated_at=data.get("updated_at"),
    )


def mark_attempt(state_path: Path, state: RunGateState) -> None:
    state_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "last_attempt_date": state.last_attempt_date,
        "last_status": state.last_status,
        "updated_at": state.updated_at,
    }
    state_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2) + "\n",
        encoding="utf-8",
    )
