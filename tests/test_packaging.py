import unittest
from pathlib import Path

from efcheck.packaging import pyinstaller_helpers


class PackagingTests(unittest.TestCase):
    def test_release_manifest_includes_required_files(self) -> None:
        manifest = pyinstaller_helpers.release_manifest("onedir")

        self.assertIn("README.md", manifest)
        self.assertIn("README.zh-TW.md", manifest)
        self.assertIn("LICENSE", manifest)
        self.assertIn("SECURITY.md", manifest)
        self.assertIn("install_efcheck.bat", manifest)
        self.assertIn("setup_windows.bat", manifest)
        self.assertIn("capture_session.bat", manifest)
        self.assertIn("run_signin.bat", manifest)
        self.assertIn("register_logon_task.bat", manifest)
        self.assertIn("register_logon_task.ps1", manifest)
        self.assertIn("config/settings.example.json", manifest)

    def test_build_layout_uses_separate_onedir_and_onefile_roots(self) -> None:
        layout = pyinstaller_helpers.build_layout(Path("C:/repo"))

        self.assertEqual(layout["onedir_dist"], Path("C:/repo/dist/pyinstaller/onedir"))
        self.assertEqual(layout["onefile_dist"], Path("C:/repo/dist/pyinstaller/onefile"))
        self.assertEqual(layout["releases_dir"], Path("C:/repo/dist/releases"))

    def test_package_release_script_uses_env_for_project_root(self) -> None:
        script = Path("packaging/package_release.ps1").read_text(encoding="utf-8")

        self.assertIn('$env:EFCHECK_PROJECT_ROOT = $projectRoot', script)
        self.assertIn('os.environ["EFCHECK_PROJECT_ROOT"]', script)

    def test_package_release_script_generates_checksum_asset(self) -> None:
        script = Path("packaging/package_release.ps1").read_text(encoding="utf-8")

        self.assertIn("EFCheck-SHA256.txt", script)
