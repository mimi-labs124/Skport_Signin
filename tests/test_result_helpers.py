import unittest

from efcheck.result_helpers import final_signin_status
from efcheck.statuses import ALREADY_DONE, ERROR, SUCCESS, UNKNOWN


class ResultHelperTests(unittest.TestCase):
    def test_success_requires_refreshed_state_to_show_already_done(self) -> None:
        status, message = final_signin_status(
            day_number=10,
            refreshed_state=ALREADY_DONE,
            post_seen=True,
        )

        self.assertEqual(status, SUCCESS)
        self.assertIn("Day 10", message)

    def test_ok_post_without_refreshed_confirmation_is_error(self) -> None:
        status, message = final_signin_status(
            day_number=10,
            refreshed_state=UNKNOWN,
            post_seen=True,
        )

        self.assertEqual(status, ERROR)
        self.assertIn("could not be verified", message)


if __name__ == "__main__":
    unittest.main()
