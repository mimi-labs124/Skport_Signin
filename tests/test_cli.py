import importlib
import io
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

from skport_signin import cli
from skport_signin.errors import ConfigError, InteractionError


class CliTests(unittest.TestCase):
    def test_python_module_entrypoint_is_available(self) -> None:
        module = importlib.import_module("skport_signin.cli")

        self.assertIs(module.main, cli.main)

    def test_top_level_help_lists_expected_commands(self) -> None:
        stdout = io.StringIO()
        with self.assertRaises(SystemExit) as cm, redirect_stdout(stdout):
            cli.main(["--help"])

        self.assertEqual(cm.exception.code, 0)
        output = stdout.getvalue()
        self.assertIn("run", output)
        self.assertIn("capture-session", output)
        self.assertIn("configure-sites", output)
        self.assertIn("register-task", output)
        self.assertIn("doctor", output)
        self.assertIn("paths", output)
        self.assertIn("package", output)
        self.assertIn("skport_signin", output)
        self.assertIn("Skport_Signin", output)

    def test_paths_json_command_runs(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            stdout = io.StringIO()
            exit_code = cli.main(
                [
                    "--base-dir",
                    str(Path(temp_dir) / "base"),
                    "paths",
                    "--json",
                ],
                stdout=stdout,
            )

        self.assertEqual(exit_code, 0)
        self.assertIn('"base_dir"', stdout.getvalue())

    def test_cli_reports_configuration_errors_cleanly(self) -> None:
        stderr = io.StringIO()

        with patch(
            "skport_signin.commands.run.handle_command",
            side_effect=ConfigError("bad config"),
        ):
            exit_code = cli.main(["run"], stderr=stderr)

        self.assertEqual(exit_code, 30)
        self.assertIn("Configuration error: bad config", stderr.getvalue())

    def test_cli_reports_runtime_errors_cleanly(self) -> None:
        stderr = io.StringIO()

        with patch(
            "skport_signin.commands.run.handle_command",
            side_effect=InteractionError("click failed"),
        ):
            exit_code = cli.main(["run"], stderr=stderr)

        self.assertEqual(exit_code, 10)
        self.assertIn("Runtime error: click failed", stderr.getvalue())

    def test_configure_sites_invalid_json_reports_configuration_error(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text("{not-json}", encoding="utf-8")
            stderr = io.StringIO()

            exit_code = cli.main(
                [
                    "--config",
                    str(config_path),
                    "configure-sites",
                    "--enable-site",
                    "endfield",
                ],
                stderr=stderr,
            )

        self.assertEqual(exit_code, 30)
        self.assertIn("Configuration error:", stderr.getvalue())
        self.assertIn("Could not parse config file", stderr.getvalue())
