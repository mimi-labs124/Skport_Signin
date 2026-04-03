import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skport_signin.daily_gate import RunGateState, mark_attempt, should_run_today
from skport_signin.errors import StateFileError


class DailyGateTests(unittest.TestCase):
    def test_gate_allows_first_run_when_state_file_is_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"

            allowed, state = should_run_today(state_path, "2026-03-22")

            self.assertTrue(allowed)
            self.assertIsNone(state.last_attempt_date)

    def test_gate_blocks_second_run_on_same_day_after_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="SUCCESS",
                    updated_at="2026-03-22T10:00:00+08:00",
                ),
            )

            allowed, state = should_run_today(state_path, "2026-03-22")

            self.assertFalse(allowed)
            self.assertEqual(state.last_status, "SUCCESS")

    def test_gate_blocks_second_run_on_same_day_after_already_done(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="ALREADY_DONE",
                    updated_at="2026-03-22T10:00:00+08:00",
                ),
            )

            allowed, state = should_run_today(state_path, "2026-03-22")

            self.assertFalse(allowed)
            self.assertEqual(state.last_status, "ALREADY_DONE")

    def test_gate_allows_second_run_on_same_day_after_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="ERROR",
                    updated_at="2026-03-22T10:00:00+08:00",
                ),
            )

            allowed, state = should_run_today(state_path, "2026-03-22")

            self.assertTrue(allowed)
            self.assertEqual(state.last_status, "ERROR")

    def test_load_state_keeps_backward_compatible_attempt_count_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text(
                '{"last_attempt_date":"2026-03-22","last_status":"ERROR","attempts_today":2}',
                encoding="utf-8",
            )

            allowed, state = should_run_today(state_path, "2026-03-22")

            self.assertTrue(allowed)
            self.assertEqual(state.last_status, "ERROR")

    def test_load_state_raises_state_file_error_for_invalid_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text("{not-json}", encoding="utf-8")

            with self.assertRaises(StateFileError):
                should_run_today(state_path, "2026-03-22")

    def test_mark_attempt_omits_attempts_today_in_new_state_file(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            mark_attempt(
                state_path,
                RunGateState(
                    last_attempt_date="2026-03-22",
                    last_status="SUCCESS",
                    updated_at="2026-03-22T10:00:00+08:00",
                ),
            )

            data = state_path.read_text(encoding="utf-8")

        self.assertNotIn("attempts_today", data)

    def test_mark_attempt_uses_atomic_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"

            with patch("skport_signin.daily_gate.write_text_atomic") as write_atomic:
                mark_attempt(
                    state_path,
                    RunGateState(
                        last_attempt_date="2026-03-22",
                        last_status="SUCCESS",
                        updated_at="2026-03-22T10:00:00+08:00",
                    ),
                )

        write_atomic.assert_called_once()
        self.assertEqual(write_atomic.call_args.args[0], state_path)

    def test_load_state_raises_state_file_error_for_nondict_json(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            state_path = Path(temp_dir) / "state.json"
            state_path.write_text("[]", encoding="utf-8")

            with self.assertRaises(StateFileError):
                should_run_today(state_path, "2026-03-22")


if __name__ == "__main__":
    unittest.main()
