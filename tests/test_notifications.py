import unittest

from efcheck.notifications import should_notify_status


class NotificationTests(unittest.TestCase):
    def test_session_expired_requires_notification(self) -> None:
        self.assertTrue(should_notify_status("SESSION_EXPIRED"))

    def test_success_does_not_require_notification(self) -> None:
        self.assertFalse(should_notify_status("SUCCESS"))


if __name__ == "__main__":
    unittest.main()
