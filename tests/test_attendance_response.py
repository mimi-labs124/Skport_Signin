import unittest

from efcheck.attendance_response import is_attendance_response


class AttendanceResponseTests(unittest.TestCase):
    def test_matches_get_attendance_endpoint(self) -> None:
        self.assertTrue(
            is_attendance_response(
                "https://zonai.skport.com/web/v1/game/endfield/attendance",
                "GET",
            )
        )

    def test_rejects_post_attendance_endpoint(self) -> None:
        self.assertFalse(
            is_attendance_response(
                "https://zonai.skport.com/web/v1/game/endfield/attendance",
                "POST",
            )
        )

    def test_rejects_unrelated_endpoint(self) -> None:
        self.assertFalse(
            is_attendance_response(
                "https://zonai.skport.com/web/v1/game/endfield/attendance/record",
                "GET",
            )
        )


if __name__ == "__main__":
    unittest.main()
