from __future__ import annotations

import argparse
import sys
from contextlib import nullcontext
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from efcheck.attendance_response import is_attendance_response
from efcheck.attendance_state import derive_attendance_state
from efcheck.browser_helpers import (
    ACTIONABLE_DESCENDANT_SELECTOR,
    day_card_selector_candidates,
    day_label_candidates,
)
from efcheck.config import SiteSettings, load_runtime_settings, resolve_path
from efcheck.daily_gate import RunGateState, load_state, mark_attempt, should_run_today
from efcheck.errors import ConfigError, InteractionError, StateFileError
from efcheck.notifications import notify_status
from efcheck.playwright_runtime import ensure_browser_runtime_available, playwright_browser_env
from efcheck.result_helpers import final_signin_status
from efcheck.runtime import RuntimeContext, build_runtime_context
from efcheck.statuses import ALREADY_DONE, ERROR, SESSION_EXPIRED, SUCCESS
from efcheck.time_helpers import load_timezone

DEFAULT_URL = "https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools"


def register_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "run",
        help="Run sign-in for all enabled sites in the current config.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show the resolved browser run details without launching a sign-in attempt.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore the per-site daily gate for this invocation.",
    )
    parser.set_defaults(handler=handle_command)


def handle_command(args, runtime: RuntimeContext) -> int:
    return run_command(runtime=runtime, dry_run=args.dry_run, force=args.force)


def run_command(*, runtime: RuntimeContext, dry_run: bool, force: bool) -> int:
    config_path = runtime.app_paths.config_file
    settings = load_runtime_settings(config_path, DEFAULT_URL)
    try:
        timezone = load_timezone(settings.timezone)
    except RuntimeError as exc:
        raise ConfigError(str(exc)) from exc

    now = datetime.now(timezone)
    log_dir = resolve_path(config_path, settings.log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    today = now.date().isoformat()
    exit_code = 0

    for site in settings.sites:
        if not site.enabled:
            continue

        state_path = resolve_path(config_path, site.state_path)
        profile_dir = resolve_path(config_path, site.browser_profile_dir)
        previous_state = load_state(state_path)

        if not force:
            allowed, previous_state = should_run_today(state_path, today)
            if not allowed:
                message = prefix_site_message(
                    site,
                    (
                        f"Skipped: already attempted on {previous_state.last_attempt_date} "
                        f"with status {previous_state.last_status}."
                    ),
                )
                write_log(log_dir, now, "SKIPPED_ALREADY_ATTEMPTED", message)
                runtime.stdout.write(message + "\n")
                continue

        if dry_run:
            message = summarize_browser_run(settings, site, profile_dir)
            write_log(log_dir, now, "DRY_RUN", message)
            runtime.stdout.write(message + "\n")
            continue

        outcome_message, status = run_browser_sign_in(
            runtime=runtime,
            profile_dir=profile_dir,
            signin_url=site.signin_url,
            attendance_path=site.attendance_path,
            headless=settings.headless,
            browser_channel=settings.browser_channel,
            timeout_seconds=settings.timeout_seconds,
        )
        prefixed_message = prefix_site_message(site, outcome_message)
        mark_attempt(
            state_path,
            RunGateState(
                last_attempt_date=today,
                last_status=status,
                updated_at=now.isoformat(),
            ),
        )
        write_log(log_dir, now, status, prefixed_message)
        notification_warning = notify_status(
            status,
            f"EFCheck session expired: {site.name}",
            (
                f"The saved sign-in session for {site.name} needs to be refreshed. "
                f"Run capture_session.bat --site {site.key}."
            ),
        )
        if notification_warning:
            write_log(
                log_dir,
                now,
                "NOTIFICATION_WARNING",
                prefix_site_message(site, notification_warning),
            )
        runtime.stdout.write(prefixed_message + "\n")
        if status not in {SUCCESS, ALREADY_DONE}:
            exit_code = 10

    return exit_code


def summarize_browser_run(settings, site: SiteSettings, profile_dir: Path) -> str:
    return (
        f"[{site.name}] Dry run only. Browser sign-in is configured for "
        f"{site.signin_url} | "
        f"profile_dir={profile_dir} | "
        f"headless={settings.headless} | "
        f"channel={settings.browser_channel} | "
        f"attendance_path={site.attendance_path}"
    )


def run_browser_sign_in(
    *,
    runtime: RuntimeContext | None = None,
    profile_dir: Path,
    signin_url: str,
    attendance_path: str,
    headless: bool,
    browser_channel: str,
    timeout_seconds: int,
) -> tuple[str, str]:
    if not profile_dir.exists():
        raise FileNotFoundError(
            f"Browser profile not found at {profile_dir}. Run capture_session.py first."
        )

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError(
            "playwright is not installed. Run `python -m pip install playwright` "
            "and then `playwright install chromium`."
        ) from exc

    timeout_ms = timeout_seconds * 1000

    browser_env = playwright_browser_env(runtime.app_paths) if runtime else nullcontext()
    with browser_env:
        with sync_playwright() as playwright:
            if runtime:
                ensure_browser_runtime_available(playwright, runtime.app_paths)
            context = playwright.chromium.launch_persistent_context(
                str(profile_dir),
                channel=browser_channel or None,
                headless=headless,
                viewport={"width": 1440, "height": 1200},
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                page.set_default_timeout(timeout_ms)
                with page.expect_response(
                    lambda response: is_attendance_response(
                        response.url,
                        response.request.method,
                        attendance_path,
                    ),
                    timeout=timeout_ms,
                ) as attendance_info:
                    page.goto(signin_url, wait_until="domcontentloaded")
                attendance_response = attendance_info.value
                if attendance_response.status in {401, 403}:
                    return (
                        "SESSION_EXPIRED: the attendance endpoint rejected the "
                        "saved browser session.",
                        SESSION_EXPIRED,
                    )
                try:
                    attendance_payload = attendance_response.json()
                except Exception:
                    attendance_payload = {"code": -1, "data": {"calendar": []}}
                page.wait_for_timeout(2000)

                state = derive_attendance_state(attendance_payload)
                if state.status == ALREADY_DONE:
                    return (
                        "ALREADY_DONE: page reports there is no available "
                        "attendance reward to claim today.",
                        ALREADY_DONE,
                    )
                if state.status == "UNKNOWN":
                    if page_looks_logged_out(page):
                        return (
                            "SESSION_EXPIRED: the browser profile no longer looks logged in.",
                            SESSION_EXPIRED,
                        )
                    return (
                        "ERROR: the attendance payload did not include a "
                        "calendar, so the run could not be verified.",
                        ERROR,
                    )

                with page.expect_response(
                    lambda response: response.request.method == "POST"
                    and urlparse(response.url).path.rstrip("/") == attendance_path.rstrip("/"),
                    timeout=timeout_ms,
                ) as post_info:
                    click_day_tile(page, state.day_number)
                post_response = post_info.value
                if post_response.status in {401, 403}:
                    return (
                        "SESSION_EXPIRED: the sign-in click was rejected because "
                        "the saved session is no longer valid.",
                        SESSION_EXPIRED,
                    )
                post_seen = post_response.ok
                with page.expect_response(
                    lambda response: is_attendance_response(
                        response.url,
                        response.request.method,
                        attendance_path,
                    ),
                    timeout=timeout_ms,
                ) as refreshed_attendance_info:
                    page.reload(wait_until="domcontentloaded")
                try:
                    attendance_payload = refreshed_attendance_info.value.json()
                except Exception:
                    pass
                try:
                    page.wait_for_timeout(2000)
                except PlaywrightTimeoutError:
                    pass
                refreshed_state = derive_attendance_state(attendance_payload)

                status, message = final_signin_status(
                    day_number=state.day_number or 0,
                    refreshed_state=refreshed_state.status,
                    post_seen=post_seen,
                )
                return message, status
            except PlaywrightTimeoutError:
                if page_looks_logged_out(page):
                    return (
                        "SESSION_EXPIRED: no attendance response arrived and the "
                        "page appears to be logged out.",
                        SESSION_EXPIRED,
                    )
                return (
                    "ERROR: timed out while waiting for attendance responses from the page.",
                    ERROR,
                )
            finally:
                context.close()


def click_day_tile(page, day_number: int | None) -> None:
    if day_number is None:
        raise InteractionError("No available day was detected to click.")
    labels = day_label_candidates(day_number)

    for selector in day_card_selector_candidates(day_number):
        container = page.locator(selector).first
        candidates = [
            container.locator(ACTIONABLE_DESCENDANT_SELECTOR).first,
            container,
        ]
        for locator in candidates:
            if try_click_locator(locator):
                return

    for text in labels:
        candidates = [
            page.get_by_text(text, exact=True).first,
            page.locator(f"text={text}").first,
            page.locator(f"div:has-text('{text}')").first,
        ]
        for locator in candidates:
            if try_click_locator(locator):
                return
    raise InteractionError(f"Could not click the tile for day {day_number}. Tried labels: {labels}")


def try_click_locator(locator) -> bool:
    try:
        locator.scroll_into_view_if_needed(timeout=2000)
        locator.click(timeout=2000, force=True)
        return True
    except Exception:
        return False


def page_looks_logged_out(page) -> bool:
    current_url = page.url.lower()
    if "login" in current_url:
        return True
    if page_has_login_form(page):
        return True

    body_text = ""
    try:
        body_text = page.locator("body").inner_text(timeout=2000).lower()
    except Exception:
        body_text = ""
    login_markers = ["login", "log in", "sign in", "\u767b\u5165", "\u767b\u5f55"]
    return any(marker in body_text for marker in login_markers)


def page_has_login_form(page) -> bool:
    selectors = [
        "input[type='password']",
        "input[name='password']",
        "input[autocomplete='current-password']",
    ]
    for selector in selectors:
        try:
            if page.locator(selector).count() > 0:
                return True
        except Exception:
            continue
    return False

def prefix_site_message(site: SiteSettings, message: str) -> str:
    return f"[{site.name}] {message}"


def write_log(log_dir: Path, now: datetime, status: str, message: str) -> None:
    log_file = log_dir / f"signin-{now.date().isoformat()}.log"
    entry = f"[{now.isoformat()}] {status} {message}\n"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(entry)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run SKPORT sign-in in a browser context."
    )
    parser.add_argument(
        "--config",
        default="config/settings.json",
        help="Path to settings.json",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse config and show a safe summary without sending the request.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Ignore the once-per-day gate for this run.",
    )
    return parser.parse_args(argv)


def legacy_main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime = build_runtime_context(config_override=args.config)
    try:
        return run_command(runtime=runtime, dry_run=args.dry_run, force=args.force)
    except FileNotFoundError as exc:
        print(f"Missing file: {exc}", file=sys.stderr)
        return 30
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 30
    except StateFileError as exc:
        print(f"State file error: {exc}", file=sys.stderr)
        return 30
    except InteractionError as exc:
        print(f"Runtime error: {exc}", file=sys.stderr)
        return 10
    except ImportError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        return 20


main = legacy_main
