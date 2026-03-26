import unittest

from efcheck.browser_helpers import day_card_selector_candidates, day_label_candidates


class BrowserHelperTests(unittest.TestCase):
    def test_day_label_candidates_cover_english_and_chinese(self) -> None:
        labels = day_label_candidates(9)

        self.assertIn("Day 9", labels)
        self.assertIn("Day9", labels)
        self.assertIn("\u7b2c9\u5929", labels)
        self.assertIn("\u7b2c 9 \u5929", labels)

    def test_day_card_selectors_include_exact_and_contains_matches(self) -> None:
        selectors = day_card_selector_candidates(9)

        self.assertTrue(any("normalize-space()='Day 9'" in selector for selector in selectors))
        self.assertTrue(any("contains(normalize-space(), 'Day9')" in selector for selector in selectors))
        self.assertTrue(any("\u7b2c9\u5929" in selector for selector in selectors))
        self.assertTrue(any("\u7b2c 9 \u5929" in selector for selector in selectors))


if __name__ == "__main__":
    unittest.main()
