import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from efcheck import app_paths


class AppPathsTests(unittest.TestCase):
    def test_source_mode_defaults_to_repo_paths(self) -> None:
        with patch.object(app_paths, "is_packaged_mode", return_value=False):
            paths = app_paths.build_app_paths()

        self.assertEqual(paths.mode, "source")
        self.assertTrue(paths.base_dir.samefile(Path.cwd()))
        self.assertEqual(paths.config_file, paths.base_dir / "config" / "settings.json")
        self.assertEqual(paths.state_dir, paths.base_dir / "state")
        self.assertEqual(paths.logs_dir, paths.base_dir / "logs")

    def test_packaged_mode_defaults_to_localappdata(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.dict(
            os.environ,
            {"LOCALAPPDATA": temp_dir},
            clear=False,
        ), patch.object(app_paths, "is_packaged_mode", return_value=True), patch.object(
            app_paths.sys,
            "executable",
            str(Path(temp_dir) / "EFCheck" / "efcheck.exe"),
        ):
            paths = app_paths.build_app_paths()

        expected_base = (Path(temp_dir) / "EFCheck").resolve()
        self.assertEqual(paths.mode, "packaged")
        self.assertEqual(paths.base_dir, expected_base)
        self.assertEqual(paths.config_file, expected_base / "config" / "settings.json")
        self.assertEqual(paths.browser_profiles_dir, expected_base / "browser-profile")
        self.assertEqual(paths.runtime_dir, expected_base / "runtime")

    def test_cli_override_wins_for_base_dir_and_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir, patch.object(
            app_paths, "is_packaged_mode", return_value=True
        ):
            base_dir = Path(temp_dir) / "custom-base"
            config_path = Path(temp_dir) / "custom-settings.json"
            paths = app_paths.build_app_paths(
                base_dir_override=str(base_dir),
                config_override=str(config_path),
            )

        self.assertEqual(paths.base_dir, base_dir.resolve())
        self.assertEqual(paths.config_file, config_path.resolve())
