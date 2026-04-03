import json
import tempfile
import unittest
from pathlib import Path

from efcheck.config import find_site, load_runtime_settings
from efcheck.errors import ConfigError


class ConfigTests(unittest.TestCase):
    def test_load_runtime_settings_normalizes_legacy_endfield_config(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps({"signin_url": "https://game.skport.com/endfield/sign-in"}),
                encoding="utf-8",
            )

            settings = load_runtime_settings(
                config_path,
                "https://game.skport.com/endfield/sign-in",
            )

        self.assertEqual(len(settings.sites), 1)
        self.assertEqual(settings.sites[0].key, "endfield")
        self.assertEqual(settings.sites[0].attendance_path, "/web/v1/game/endfield/attendance")

    def test_load_runtime_settings_parses_multiple_sites(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "browser_profile_dir": "../state/shared-profile",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "browser_profile_dir": "../state/shared-profile",
                                "enabled": True,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            settings = load_runtime_settings(
                config_path,
                "https://game.skport.com/endfield/sign-in",
            )

        self.assertEqual([site.key for site in settings.sites], ["endfield", "arknights"])
        self.assertEqual(settings.sites[1].attendance_path, "/api/v1/game/attendance")
        self.assertEqual(
            settings.sites[0].browser_profile_dir,
            settings.sites[1].browser_profile_dir,
        )
        self.assertFalse(hasattr(settings, "max_attempts_per_day"))

    def test_load_runtime_settings_derives_arknights_attendance_path(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            settings = load_runtime_settings(
                config_path,
                "https://game.skport.com/endfield/sign-in",
            )

        self.assertEqual(settings.sites[0].attendance_path, "/api/v1/game/attendance")

    def test_find_site_matches_by_key_or_name(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            settings = load_runtime_settings(
                config_path,
                "https://game.skport.com/endfield/sign-in",
            )

        self.assertEqual(find_site(settings, "arknights").name, "Arknights")
        self.assertEqual(find_site(settings, "Endfield").key, "endfield")

    def test_load_runtime_settings_requires_real_json_boolean(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps({"headless": "false"}),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_runtime_settings(config_path, "https://example.com")

    def test_load_runtime_settings_rejects_non_string_signin_url(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps({"signin_url": 123}),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_runtime_settings(config_path, "https://example.com")

    def test_load_runtime_settings_rejects_nonpositive_timeout(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps({"timeout_seconds": 0}),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_runtime_settings(config_path, "https://example.com")

    def test_load_runtime_settings_ignores_legacy_max_attempts_field(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps({"max_attempts_per_day": 0}),
                encoding="utf-8",
            )

            settings = load_runtime_settings(
                config_path,
                "https://game.skport.com/endfield/sign-in",
            )

        self.assertEqual(settings.sites[0].key, "endfield")

    def test_load_runtime_settings_allows_disabled_known_sites(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "enabled": True,
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "enabled": False,
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            settings = load_runtime_settings(config_path, "https://example.com")

        self.assertEqual([site.enabled for site in settings.sites], [True, False])

    def test_load_runtime_settings_rejects_unknown_sites_shape(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            config_path = Path(temp_dir) / "settings.json"
            config_path.write_text(
                json.dumps({"sites": []}),
                encoding="utf-8",
            )

            with self.assertRaises(ConfigError):
                load_runtime_settings(config_path, "https://example.com")


if __name__ == "__main__":
    unittest.main()
