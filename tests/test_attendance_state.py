import unittest

from efcheck.attendance_state import derive_attendance_state


class AttendanceStateTests(unittest.TestCase):
    def test_ready_to_sign_when_calendar_has_available_reward(self) -> None:
        payload = {
            "code": 0,
            "data": {
                "calendar": [
                    {"available": False, "done": True},
                    {"available": True, "done": False},
                    {"available": False, "done": False},
                ]
            },
        }

        result = derive_attendance_state(payload)

        self.assertEqual(result.status, "READY_TO_SIGN")
        self.assertEqual(result.day_number, 2)

    def test_already_done_when_no_available_reward_exists(self) -> None:
        payload = {
            "code": 0,
            "data": {
                "calendar": [
                    {"available": False, "done": True},
                    {"available": False, "done": True},
                    {"available": False, "done": False},
                ]
            },
        }

        result = derive_attendance_state(payload)

        self.assertEqual(result.status, "ALREADY_DONE")
        self.assertIsNone(result.day_number)

    def test_unknown_when_calendar_is_missing(self) -> None:
        payload = {"code": 0, "data": {"records": []}}

        result = derive_attendance_state(payload)

        self.assertEqual(result.status, "UNKNOWN")


if __name__ == "__main__":
    unittest.main()
