from __future__ import annotations

import argparse
from pathlib import Path
import json
import sys


DEFAULT_CONFIG = Path("config/settings.json")
DEFAULT_URL = "https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools"


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()
    settings = json.loads(config_path.read_text(encoding="utf-8"))
    profile_dir = resolve_path(
        config_path,
        settings.get("browser_profile_dir", "../state/browser-profile"),
    )
    signin_url = settings.get("signin_url", DEFAULT_URL)
    channel = settings.get("browser_channel", "")

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        print(
            "Missing dependency: playwright is not installed. "
            "Run `python -m pip install playwright` and then `playwright install chromium`.",
            file=sys.stderr,
        )
        return 20

    profile_dir.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        context = playwright.chromium.launch_persistent_context(
            str(profile_dir),
            channel=channel or None,
            headless=False,
            viewport={"width": 1440, "height": 1200},
        )
        page = context.pages[0] if context.pages else context.new_page()
        page.goto(signin_url, wait_until="domcontentloaded")
        input(
            "Log in in the opened browser window. When the page shows your sign-in dashboard, press Enter here to save the session."
        )
        context.close()
    print(f"Saved browser session in {profile_dir}")
    return 0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a browser session for EFCheck.")
    parser.add_argument("--config", default=str(DEFAULT_CONFIG), help="Path to settings.json")
    return parser.parse_args()


def resolve_path(config_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (config_path.parent / candidate).resolve()


if __name__ == "__main__":
    raise SystemExit(main())
