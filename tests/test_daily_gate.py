import tempfile
import unittest
from pathlib import Path

from efcheck.daily_gate import RunGateState, mark_attempt, should_run_today


class DailyGateTests(unittest.TestCase):
    def test_gate_allows_first_run_when_state_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"

            allowed, state = should_run_today(state_path, "2026-03-22")

            self.assertTrue(allowed)
            self.assertIsNone(state.last_attempt_date)

    def test_gate_blocks_second_run_on_same_day(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="SUCCESS",
                    attempts_today=1,
                    updated_at="2026-03-22T10:00:00+08:00",
                ),
            )

            allowed, state = should_run_today(state_path, "2026-03-22", max_attempts_per_day=2)

            self.assertFalse(allowed)
            self.assertEqual(state.last_status, "SUCCESS")

    def test_gate_allows_second_attempt_after_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="ERROR",
                    attempts_today=1,
                    updated_at="2026-03-22T10:00:00+08:00",
                ),
            )

            allowed, state = should_run_today(state_path, "2026-03-22", max_attempts_per_day=2)

            self.assertTrue(allowed)
            self.assertEqual(state.attempts_today, 1)

    def test_gate_blocks_third_attempt_after_two_failures(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="ERROR",
                    attempts_today=2,
                    updated_at="2026-03-22T11:00:00+08:00",
                ),
            )

            allowed, _ = should_run_today(state_path, "2026-03-22", max_attempts_per_day=2)

            self.assertFalse(allowed)


if __name__ == "__main__":
    unittest.main()
