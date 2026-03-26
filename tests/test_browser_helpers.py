import unittest

from efcheck.browser_helpers import day_label_candidates


class BrowserHelperTests(unittest.TestCase):
    def test_day_label_candidates_cover_english_and_chinese(self) -> None:
        labels = day_label_candidates(9)

        self.assertIn("Day 9", labels)
        self.assertIn("Day9", labels)
        self.assertIn("第9天", labels)


if __name__ == "__main__":
    unittest.main()
