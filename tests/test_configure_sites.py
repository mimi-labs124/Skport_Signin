import json
import tempfile
import unittest
from pathlib import Path

from efcheck.commands import configure_sites


class ConfigureSitesTests(unittest.TestCase):
    def test_configure_sites_writes_known_sites_with_endfield_enabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "timezone": "Asia/Taipei",
                        "headless": True,
                        "sites": [],
                    }
                ),
                encoding="utf-8",
            )

            configure_sites.configure_sites(
                config_path,
                enabled_sites={"endfield"},
                share_profile_with_arknights=True,
            )

            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual([site["key"] for site in data["sites"]], ["endfield", "arknights"])
        self.assertEqual([site["enabled"] for site in data["sites"]], [True, False])
        self.assertEqual(data["sites"][0]["browser_profile_dir"], "../state/browser-profile")
        self.assertEqual(
            data["sites"][1]["browser_profile_dir"],
            "../state/arknights-browser-profile",
        )

    def test_configure_sites_can_enable_arknights_with_shared_profile(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text("{}", encoding="utf-8")

            configure_sites.configure_sites(
                config_path,
                enabled_sites={"endfield", "arknights"},
                share_profile_with_arknights=True,
            )

            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual([site["key"] for site in data["sites"]], ["endfield", "arknights"])
        self.assertEqual([site["enabled"] for site in data["sites"]], [True, True])
        self.assertEqual(
            data["sites"][0]["browser_profile_dir"],
            data["sites"][1]["browser_profile_dir"],
        )
        self.assertEqual(data["sites"][1]["attendance_path"], "/api/v1/game/attendance")

    def test_configure_sites_can_disable_endfield(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text("{}", encoding="utf-8")

            configure_sites.configure_sites(
                config_path,
                enabled_sites={"arknights"},
                share_profile_with_arknights=False,
            )

            data = json.loads(config_path.read_text(encoding="utf-8"))

        self.assertEqual([site["enabled"] for site in data["sites"]], [False, True])
        self.assertEqual(
            data["sites"][1]["browser_profile_dir"],
            "../state/arknights-browser-profile",
        )


if __name__ == "__main__":
    unittest.main()
