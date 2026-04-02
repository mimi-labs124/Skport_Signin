from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from efcheck.config import derive_attendance_path
from efcheck.errors import ConfigError


DEFAULT_CONFIG = Path("config/settings.json")
ENDFIELD_SIGNIN_URL = "https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools"
ARKNIGHTS_SIGNIN_URL = "https://game.skport.com/arknights/sign-in"


def configure_sites(
    config_path: Path,
    *,
    include_arknights: bool,
    share_profile_with_arknights: bool,
) -> None:
    data = _load_existing_config(config_path)

    data["sites"] = build_sites(
        include_arknights=include_arknights,
        share_profile_with_arknights=share_profile_with_arknights,
    )

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def build_sites(*, include_arknights: bool, share_profile_with_arknights: bool) -> list[dict]:
    endfield = {
        "key": "endfield",
        "name": "Endfield",
        "enabled": True,
        "signin_url": ENDFIELD_SIGNIN_URL,
        "attendance_path": derive_attendance_path(ENDFIELD_SIGNIN_URL),
        "state_path": "../state/endfield-last_run.json",
        "browser_profile_dir": "../state/browser-profile",
    }
    sites = [endfield]

    if include_arknights:
        sites.append(
            {
                "key": "arknights",
                "name": "Arknights",
                "enabled": True,
                "signin_url": ARKNIGHTS_SIGNIN_URL,
                "attendance_path": derive_attendance_path(ARKNIGHTS_SIGNIN_URL),
                "state_path": "../state/arknights-last_run.json",
                "browser_profile_dir": (
                    "../state/browser-profile"
                    if share_profile_with_arknights
                    else "../state/arknights-browser-profile"
                ),
            }
        )

    return sites


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure EFCheck sites for guided setup.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to settings.json")
    parser.add_argument(
        "--include-arknights",
        action="store_true",
        help="Add the Arknights SKPORT sign-in page to the configured sites.",
    )
    parser.add_argument(
        "--share-arknights-profile",
        action="store_true",
        help="Use the same browser profile directory for Endfield and Arknights.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    try:
        configure_sites(
            Path(args.config).resolve(),
            include_arknights=args.include_arknights,
            share_profile_with_arknights=args.share_arknights_profile,
        )
    except FileNotFoundError as exc:
        print(f"Missing file: {exc}", file=sys.stderr)
        return 30
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 30

    print("Configured EFCheck sites.")
    return 0


def _load_existing_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Could not parse config file at {config_path}: {exc.msg}.") from exc
    if not isinstance(data, dict):
        raise ConfigError(f"Configuration file at {config_path} must contain a JSON object.")
    return {
        key: value
        for key, value in data.items()
        if key
        in {
            "timezone",
            "log_dir",
            "browser_channel",
            "headless",
            "timeout_seconds",
            "max_attempts_per_day",
        }
    }


if __name__ == "__main__":
    raise SystemExit(main())
