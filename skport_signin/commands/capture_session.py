from __future__ import annotations

import argparse
import sys

from skport_signin.config import (
    find_site,
    load_runtime_settings,
    resolve_path,
)
from skport_signin.errors import ConfigError
from skport_signin.playwright_runtime import (
    ensure_browser_runtime_available,
    playwright_browser_env,
)
from skport_signin.runtime import RuntimeContext, build_runtime_context

DEFAULT_URL = "https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools"


def register_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "capture-session",
        help="Open a real browser window and save the login session profile.",
    )
    parser.add_argument(
        "--site",
        help="Site key or name to capture a session for. If omitted, captures all enabled sites.",
    )
    parser.set_defaults(handler=handle_command)


def handle_command(args, runtime: RuntimeContext) -> int:
    return run_capture_sessions(runtime=runtime, site_name=args.site)


def run_capture_sessions(*, runtime: RuntimeContext, site_name: str | None) -> int:
    config_path = runtime.app_paths.config_file
    settings = load_runtime_settings(config_path, DEFAULT_URL)
    if site_name:
        selected_sites = [find_site(settings, site_name)]
    else:
        selected_sites = [site for site in settings.sites if site.enabled]

    for site in selected_sites:
        exit_code = run_capture_session(runtime=runtime, site_name=site.key)
        if exit_code != 0:
            return exit_code
    return 0


def run_capture_session(*, runtime: RuntimeContext, site_name: str) -> int:
    config_path = runtime.app_paths.config_file
    settings = load_runtime_settings(config_path, DEFAULT_URL)
    site = find_site(settings, site_name)
    profile_dir = resolve_path(config_path, site.browser_profile_dir)
    signin_url = site.signin_url
    channel = settings.browser_channel

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Missing dependency: playwright is not installed. "
            "Run `python -m pip install playwright` and then "
            "`playwright install chromium`.",
            file=runtime.stderr,
        )
        return 20

    profile_dir.mkdir(parents=True, exist_ok=True)
    with playwright_browser_env(runtime.app_paths):
        with sync_playwright() as playwright:
            ensure_browser_runtime_available(playwright, runtime.app_paths)
            context = playwright.chromium.launch_persistent_context(
                str(profile_dir),
                channel=channel or None,
                headless=False,
                viewport={"width": 1440, "height": 1200},
            )
            page = context.pages[0] if context.pages else context.new_page()
            page.goto(signin_url, wait_until="domcontentloaded")
            input(
                "Log in in the opened browser window. When the page shows your "
                "sign-in dashboard, press Enter here to save the session."
            )
            context.close()
    runtime.stdout.write(f"Saved browser session in {profile_dir}\n")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Capture a browser session for SKPORT Sign-in.")
    parser.add_argument(
        "--config",
        default="config/settings.json",
        help="Path to settings.json",
    )
    parser.add_argument(
        "--site",
        help="Site key or name to capture a session for. If omitted, captures all enabled sites.",
    )
    return parser.parse_args(argv)


def legacy_main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime = build_runtime_context(config_override=args.config)
    try:
        return run_capture_sessions(runtime=runtime, site_name=args.site)
    except FileNotFoundError as exc:
        print(f"Missing file: {exc}", file=sys.stderr)
        return 30
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 30


main = legacy_main
