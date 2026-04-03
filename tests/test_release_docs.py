import unittest
from pathlib import Path


class ReleaseDocsTests(unittest.TestCase):
    def test_required_docs_exist(self) -> None:
        required_files = [
            Path("CHANGELOG.md"),
            Path("CONTRIBUTING.md"),
            Path("docs/release.md"),
            Path("docs/packaging.md"),
            Path("docs/repo-metadata.md"),
            Path(".github/ISSUE_TEMPLATE/config.yml"),
            Path(".github/ISSUE_TEMPLATE/bug_report.yml"),
            Path(".github/ISSUE_TEMPLATE/bug_report.md"),
            Path(".github/ISSUE_TEMPLATE/feature_request.md"),
            Path(".github/pull_request_template.md"),
        ]

        for path in required_files:
            self.assertTrue(path.exists(), f"Missing required doc file: {path}")

    def test_ci_covers_windows_ruff_tests_and_packaging_smoke(self) -> None:
        ci_text = Path(".github/workflows/ci.yml").read_text(encoding="utf-8")

        self.assertIn("windows-latest", ci_text)
        self.assertIn("ruff", ci_text)
        self.assertIn("python -m unittest discover -s tests", ci_text)
        self.assertIn("packaging-smoke-windows", ci_text)
        self.assertIn("python -m efcheck package onedir", ci_text)
        self.assertIn("efcheck.exe --help", ci_text)
