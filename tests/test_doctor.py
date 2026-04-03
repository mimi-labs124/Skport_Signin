import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from skport_signin import cli
from skport_signin.app_paths import build_app_paths
from skport_signin.default_settings import write_default_settings


class DoctorTests(unittest.TestCase):
    def test_init_creates_default_config_in_base_dir(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "portable"
            stdout = io.StringIO()

            exit_code = cli.main(
                [
                    "--base-dir",
                    str(base_dir),
                    "init",
                ],
                stdout=stdout,
            )

            config_path = base_dir / "config" / "settings.json"
            self.assertTrue(config_path.exists())
            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual(exit_code, 0)
        self.assertEqual(data["sites"][0]["key"], "endfield")

    def test_doctor_json_reports_missing_config_and_runtime_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "portable"
            stdout = io.StringIO()

            exit_code = cli.main(
                [
                    "--base-dir",
                    str(base_dir),
                    "doctor",
                    "--json",
                ],
                stdout=stdout,
            )

        self.assertEqual(exit_code, 0)
        payload = json.loads(stdout.getvalue())
        self.assertFalse(payload["config_exists"])
        self.assertIn("playwright_browsers_dir", payload["paths"])

    def test_write_default_settings_uses_atomic_write(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "portable"
            paths = build_app_paths(base_dir_override=str(base_dir))

            with patch("skport_signin.default_settings.write_text_atomic") as write_atomic:
                config_path = write_default_settings(paths, force=True)

        write_atomic.assert_called_once()
        self.assertEqual(write_atomic.call_args.args[0], config_path)
