import io
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from efcheck import cli
from efcheck.runtime import RuntimeContext


class SmokeCliTests(unittest.TestCase):
    def test_init_doctor_and_paths_smoke(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            base_dir = Path(temp_dir) / "portable"

            init_stdout = io.StringIO()
            self.assertEqual(
                cli.main(["--base-dir", str(base_dir), "init"], stdout=init_stdout),
                0,
            )

            doctor_stdout = io.StringIO()
            self.assertEqual(
                cli.main(["--base-dir", str(base_dir), "doctor", "--json"], stdout=doctor_stdout),
                0,
            )

            paths_stdout = io.StringIO()
            self.assertEqual(
                cli.main(["--base-dir", str(base_dir), "paths", "--json"], stdout=paths_stdout),
                0,
            )

            config_path = base_dir / "config" / "settings.json"
            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual([site["key"] for site in data["sites"]], ["endfield", "arknights"])
        self.assertEqual([site["enabled"] for site in data["sites"]], [True, False])

    def test_package_subcommands_dispatch_to_builder(self) -> None:
        with patch(
            "efcheck.commands.package.build_pyinstaller",
            return_value=Path("dist"),
        ) as build_mock:
            stdout = io.StringIO()
            exit_code = cli.main(["package", "onedir"], stdout=stdout)

        self.assertEqual(exit_code, 0)
        build_mock.assert_called_once()
        self.assertIn("Built onedir package", stdout.getvalue())

    def test_package_subcommands_reject_packaged_mode(self) -> None:
        runtime = RuntimeContext(
            app_paths=type(
                "Paths",
                (),
                {
                    "mode": "packaged",
                    "bundle_root": Path("dist"),
                },
            )(),
            stdout=io.StringIO(),
            stderr=io.StringIO(),
        )

        with patch("efcheck.cli.build_runtime_context", return_value=runtime):
            exit_code = cli.main(["package", "onedir"])

        self.assertEqual(exit_code, 20)
        self.assertIn("Packaging is only supported", runtime.stderr.getvalue())
