from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
import json
import sys

from efcheck.attendance_state import derive_attendance_state
from efcheck.attendance_response import is_attendance_response
from efcheck.browser_helpers import (
    ACTIONABLE_DESCENDANT_SELECTOR,
    day_card_selector_candidates,
    day_label_candidates,
)
from efcheck.daily_gate import RunGateState, load_state, mark_attempt, should_run_today
from efcheck.notifications import notify_status
from efcheck.result_helpers import final_signin_status
from efcheck.statuses import ALREADY_DONE, ERROR, READY_TO_SIGN, SESSION_EXPIRED, SUCCESS, UNKNOWN
from efcheck.time_helpers import load_timezone


DEFAULT_CONFIG = Path("config/settings.json")
DEFAULT_URL = "https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools"


def main() -> int:
    args = parse_args()
    config_path = Path(args.config).resolve()

    try:
        settings = load_settings(config_path)
        now = datetime.now(load_timezone(settings["timezone"]))
        state_path = resolve_path(config_path, settings["state_path"])
        log_dir = resolve_path(config_path, settings["log_dir"])
        profile_dir = resolve_path(config_path, settings["browser_profile_dir"])
        log_dir.mkdir(parents=True, exist_ok=True)
        today = now.date().isoformat()
        previous_state = load_state(state_path)

        if not args.force:
            allowed, previous_state = should_run_today(
                state_path,
                today,
                max_attempts_per_day=settings["max_attempts_per_day"],
            )
            if not allowed:
                message = (
                    f"Skipped: already attempted on {previous_state.last_attempt_date} "
                    f"with status {previous_state.last_status} "
                    f"({previous_state.attempts_today}/{settings['max_attempts_per_day']} attempts today)."
                )
                write_log(
                    log_dir,
                    now,
                    "SKIPPED_ALREADY_ATTEMPTED",
                    message,
                )
                print(message)
                return 0

        if args.dry_run:
            message = summarize_browser_run(settings, profile_dir)
            write_log(log_dir, now, "DRY_RUN", message)
            print(message)
            return 0

        outcome_message, status = run_browser_sign_in(
            profile_dir=profile_dir,
            signin_url=settings["signin_url"],
            headless=settings["headless"],
            browser_channel=settings["browser_channel"],
            timeout_seconds=settings["timeout_seconds"],
        )
        mark_attempt(
            state_path,
            RunGateState(
                last_attempt_date=today,
                last_status=status,
                attempts_today=next_attempt_count(previous_state, today),
                updated_at=now.isoformat(),
            ),
        )
        write_log(log_dir, now, status, outcome_message)
        notify_status(
            status,
            "EFCheck session expired",
            "The saved sign-in session needs to be refreshed. Run capture_session.bat.",
        )
        print(outcome_message)
        return 0 if status in {SUCCESS, ALREADY_DONE} else 10
    except FileNotFoundError as exc:
        print(f"Missing file: {exc}", file=sys.stderr)
        return 30
    except ValueError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 30
    except ImportError as exc:
        print(f"Missing dependency: {exc}", file=sys.stderr)
        return 20


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run Endfield sign-in in a browser context."
    )
    parser.add_argument(
        "--config",
        default=str(DEFAULT_CONFIG),
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
    return parser.parse_args()


def load_settings(config_path: Path) -> dict:
    data = json.loads(config_path.read_text(encoding="utf-8"))
    return {
        "timezone": data.get("timezone", "Asia/Taipei"),
        "signin_url": data.get("signin_url", DEFAULT_URL),
        "state_path": data.get("state_path", "../state/last_run.json"),
        "log_dir": data.get("log_dir", "../logs"),
        "browser_profile_dir": data.get("browser_profile_dir", "../state/browser-profile"),
        "browser_channel": data.get("browser_channel", ""),
        "headless": bool(data.get("headless", True)),
        "timeout_seconds": int(data.get("timeout_seconds", 20)),
        "max_attempts_per_day": int(data.get("max_attempts_per_day", 2)),
    }


def resolve_path(config_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (config_path.parent / candidate).resolve()


def summarize_browser_run(settings: dict, profile_dir: Path) -> str:
    return (
        "Dry run only. Browser sign-in is configured for "
        f"{settings['signin_url']} | "
        f"profile_dir={profile_dir} | "
        f"headless={settings['headless']} | "
        f"channel={settings['browser_channel']}"
    )


def run_browser_sign_in(
    *,
    profile_dir: Path,
    signin_url: str,
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
            "playwright is not installed. Run `python -m pip install playwright` and then `playwright install chromium`."
        ) from exc

    timeout_ms = timeout_seconds * 1000

    with sync_playwright() as playwright:
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
                ),
                timeout=timeout_ms,
            ) as attendance_info:
                page.goto(signin_url, wait_until="domcontentloaded")
            attendance_response = attendance_info.value
            if attendance_response.status in {401, 403}:
                return (
                    "SESSION_EXPIRED: the attendance endpoint rejected the saved browser session.",
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
                    "ALREADY_DONE: page reports there is no available attendance reward to claim today.",
                    ALREADY_DONE,
                )
            if state.status == UNKNOWN:
                if page_looks_logged_out(page):
                    return (
                        "SESSION_EXPIRED: the browser profile no longer looks logged in.",
                        SESSION_EXPIRED,
                    )
                return (
                    "ERROR: the attendance payload did not include a calendar, so the run could not be verified.",
                    ERROR,
                )

            with page.expect_response(
                lambda response: response.request.method == "POST"
                and response.url.rstrip("/").endswith("/web/v1/game/endfield/attendance"),
                timeout=timeout_ms,
            ) as post_info:
                click_day_tile(page, state.day_number)
            post_response = post_info.value
            if post_response.status in {401, 403}:
                return (
                    "SESSION_EXPIRED: the sign-in click was rejected because the saved session is no longer valid.",
                    SESSION_EXPIRED,
                )
            post_seen = post_response.ok
            with page.expect_response(
                lambda response: is_attendance_response(
                    response.url,
                    response.request.method,
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

            return final_signin_status(
                day_number=state.day_number or 0,
                refreshed_state=refreshed_state.status,
                post_seen=post_seen,
            )
        except PlaywrightTimeoutError:
            if page_looks_logged_out(page):
                return (
                    "SESSION_EXPIRED: no attendance response arrived and the page appears to be logged out.",
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
        raise ValueError("No available day was detected to click.")
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
    raise ValueError(f"Could not click the tile for day {day_number}. Tried labels: {labels}")


def try_click_locator(locator) -> bool:
    try:
        locator.scroll_into_view_if_needed(timeout=2000)
        locator.click(timeout=2000, force=True)
        return True
    except Exception:
        return False


def page_looks_logged_out(page) -> bool:
    current_url = page.url.lower()
    body_text = ""
    try:
        body_text = page.locator("body").inner_text(timeout=2000).lower()
    except Exception:
        body_text = ""
    login_markers = ["login", "log in", "sign in", "登入", "登录", "account"]
    return "login" in current_url or any(marker in body_text for marker in login_markers)


def next_attempt_count(previous_state: RunGateState, today: str) -> int:
    if previous_state.last_attempt_date == today:
        return previous_state.attempts_today + 1
    return 1


def write_log(log_dir: Path, now: datetime, status: str, message: str) -> None:
    log_file = log_dir / f"signin-{now.date().isoformat()}.log"
    entry = f"[{now.isoformat()}] {status} {message}\n"
    with log_file.open("a", encoding="utf-8") as handle:
        handle.write(entry)


if __name__ == "__main__":
    raise SystemExit(main())
