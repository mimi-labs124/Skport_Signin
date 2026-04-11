from __future__ import annotations

import argparse
import sys
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from skport_signin.attendance_response import is_attendance_response
from skport_signin.attendance_state import derive_attendance_state
from skport_signin.browser_helpers import (
    ACTIONABLE_DESCENDANT_SELECTOR,
    day_card_selector_candidates,
    day_label_candidates,
)
from skport_signin.config import SiteSettings, load_runtime_settings, resolve_path
from skport_signin.daily_gate import (
    RunGateState,
    mark_attempt,
    should_run_today,
)
from skport_signin.errors import ConfigError, InteractionError, StateFileError
from skport_signin.notifications import notify_status
from skport_signin.playwright_runtime import (
    ensure_browser_runtime_available,
    playwright_browser_env,
)
from skport_signin.result_helpers import final_signin_status
from skport_signin.runtime import RuntimeContext, build_runtime_context
from skport_signin.statuses import ALREADY_DONE, ERROR, SESSION_EXPIRED, SUCCESS, UNKNOWN
from skport_signin.time_helpers import load_timezone

DEFAULT_URL = "https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools"
REFRESH_VERIFICATION_ATTEMPTS = 3
REFRESH_VERIFICATION_DELAY_MS = 1500


@dataclass(frozen=True)
class PendingSiteRun:
    site: SiteSettings
    state_path: Path
    profile_dir: Path


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
    pending_runs: list[PendingSiteRun] = []

    for site in settings.sites:
        if not site.enabled:
            continue

        state_path = resolve_path(config_path, site.state_path)
        profile_dir = resolve_path(config_path, site.browser_profile_dir)

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
                write_log(
                    log_dir,
                    now,
                    "SKIPPED_ALREADY_ATTEMPTED",
                    message,
                    details=site_log_details(site=site, profile_dir=profile_dir),
                )
                runtime.stdout.write(message + "\n")
                continue

        if dry_run:
            message = summarize_browser_run(settings, site, profile_dir)
            write_log(
                log_dir,
                now,
                "DRY_RUN",
                message,
                details=site_log_details(site=site, profile_dir=profile_dir),
            )
            runtime.stdout.write(message + "\n")
            continue

        pending_runs.append(
            PendingSiteRun(
                site=site,
                state_path=state_path,
                profile_dir=profile_dir,
            )
        )

    for group in group_pending_runs_by_profile(pending_runs):
        for pending_run in group:
            write_log(
                log_dir,
                datetime.now(timezone),
                "SITE_STARTED",
                prefix_site_message(pending_run.site, "Starting sign-in attempt."),
                details=site_log_details(
                    site=pending_run.site,
                    profile_dir=pending_run.profile_dir,
                ),
            )
        if len(group) == 1:
            results = [
                run_single_pending_site(
                    runtime=runtime,
                    settings=settings,
                    pending_run=group[0],
                )
            ]
        else:
            results = run_browser_sign_in_group(
                runtime=runtime,
                settings=settings,
                pending_runs=group,
            )
        for pending_run, outcome_message, status in results:
            result_now = datetime.now(timezone)
            prefixed_message = prefix_site_message(pending_run.site, outcome_message)
            mark_attempt(
                pending_run.state_path,
                RunGateState(
                    last_attempt_date=today,
                    last_status=status,
                    updated_at=result_now.isoformat(),
                ),
            )
            write_log(
                log_dir,
                result_now,
                status,
                prefixed_message,
                details=site_log_details(
                    site=pending_run.site,
                    profile_dir=pending_run.profile_dir,
                ),
            )
            notification_title, notification_message = build_notification_content(
                pending_run=pending_run,
                status=status,
            )
            notification_warning = notify_status(status, notification_title, notification_message)
            if notification_warning:
                write_log(
                    log_dir,
                    result_now,
                    "NOTIFICATION_WARNING",
                    prefix_site_message(pending_run.site, notification_warning),
                    details=site_log_details(
                        site=pending_run.site,
                        profile_dir=pending_run.profile_dir,
                    ),
                )
            runtime.stdout.write(prefixed_message + "\n")
            if status not in {SUCCESS, ALREADY_DONE}:
                exit_code = 10

    return exit_code


def group_pending_runs_by_profile(
    pending_runs: list[PendingSiteRun],
) -> list[list[PendingSiteRun]]:
    grouped: dict[Path, list[PendingSiteRun]] = {}
    for pending_run in pending_runs:
        grouped.setdefault(pending_run.profile_dir, []).append(pending_run)
    return list(grouped.values())


def run_browser_sign_in_group(
    *,
    runtime: RuntimeContext,
    settings,
    pending_runs: list[PendingSiteRun],
) -> list[tuple[PendingSiteRun, str, str]]:
    if not pending_runs:
        return []

    profile_dir = pending_runs[0].profile_dir
    if not profile_dir.exists():
        raise FileNotFoundError(
            f"Browser profile not found at {profile_dir}. "
            "Run 'skport_signin capture-session' first."
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError(
            "playwright is not installed. Run `python -m pip install playwright` "
            "and then `playwright install chromium`."
        ) from exc

    browser_env = playwright_browser_env(runtime.app_paths)
    with browser_env:
        with sync_playwright() as playwright:
            ensure_browser_runtime_available(playwright, runtime.app_paths)
            context = playwright.chromium.launch_persistent_context(
                str(profile_dir),
                channel=settings.browser_channel or None,
                headless=settings.headless,
                viewport={"width": 1440, "height": 1200},
            )
            try:
                results = []
                for pending_run in pending_runs:
                    results.append(
                        run_pending_site_in_context(
                            pending_run=pending_run,
                            context=context,
                            timeout_seconds=settings.timeout_seconds,
                        )
                    )
                return results
            finally:
                context.close()


def run_single_pending_site(
    *,
    runtime: RuntimeContext,
    settings,
    pending_run: PendingSiteRun,
) -> tuple[PendingSiteRun, str, str]:
    try:
        return (
            pending_run,
            *run_browser_sign_in(
                runtime=runtime,
                profile_dir=pending_run.profile_dir,
                signin_url=pending_run.site.signin_url,
                attendance_path=pending_run.site.attendance_path,
                headless=settings.headless,
                browser_channel=settings.browser_channel,
                timeout_seconds=settings.timeout_seconds,
            ),
        )
    except Exception as exc:
        return pending_run, format_site_runtime_exception(exc), ERROR


def run_pending_site_in_context(
    *,
    pending_run: PendingSiteRun,
    context,
    timeout_seconds: int,
) -> tuple[PendingSiteRun, str, str]:
    try:
        return (
            pending_run,
            *run_browser_sign_in_in_context(
                context=context,
                signin_url=pending_run.site.signin_url,
                attendance_path=pending_run.site.attendance_path,
                timeout_seconds=timeout_seconds,
            ),
        )
    except Exception as exc:
        return pending_run, format_site_runtime_exception(exc), ERROR


def format_site_runtime_exception(exc: Exception) -> str:
    return (
        "ERROR: unhandled runtime exception during sign-in attempt: "
        f"{type(exc).__name__}: {exc}"
    )


def build_notification_content(
    *,
    pending_run: PendingSiteRun,
    status: str,
) -> tuple[str, str]:
    if status == SESSION_EXPIRED:
        return (
            f"SKPORT Sign-in session expired: {pending_run.site.name}",
            (
                f"The saved sign-in session for {pending_run.site.name} needs to be refreshed. "
                f"Run: skport_signin capture-session --site {pending_run.site.key}"
            ),
        )
    return (
        f"SKPORT Sign-in failed: {pending_run.site.name}",
        (
            f"{pending_run.site.name} sign-in did not complete successfully. "
            f"Check the latest sign-in log and refresh the session if needed. "
            f"Run: skport_signin capture-session --site {pending_run.site.key}"
        ),
    )


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
            f"Browser profile not found at {profile_dir}. "
            "Run 'skport_signin capture-session' first."
        )

    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise ImportError(
            "playwright is not installed. Run `python -m pip install playwright` "
            "and then `playwright install chromium`."
        ) from exc

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
                return run_browser_sign_in_in_context(
                    context=context,
                    signin_url=signin_url,
                    attendance_path=attendance_path,
                    timeout_seconds=timeout_seconds,
                )
            finally:
                context.close()


def run_browser_sign_in_in_context(
    *,
    context,
    signin_url: str,
    attendance_path: str,
    timeout_seconds: int,
) -> tuple[str, str]:
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    timeout_ms = timeout_seconds * 1000
    page = context.new_page()
    page.set_default_timeout(timeout_ms)

    try:
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
                f"saved browser session. response_status={attendance_response.status} "
                f"final_url={safe_page_url(page)}",
                SESSION_EXPIRED,
            )
        try:
            attendance_payload = attendance_response.json()
        except (ValueError, TypeError, PlaywrightError):
            attendance_payload = {"code": -1, "data": {"calendar": []}}
        page.wait_for_timeout(2000)

        state = derive_attendance_state(attendance_payload)
        if state.status == ALREADY_DONE:
            return (
                "ALREADY_DONE: page reports there is no available "
                "attendance reward to claim today.",
                ALREADY_DONE,
            )
        if state.status == UNKNOWN:
            if page_looks_logged_out(page):
                return (
                    "SESSION_EXPIRED: the browser profile no longer looks logged in. "
                    f"final_url={safe_page_url(page)}",
                    SESSION_EXPIRED,
                )
            return (
                "ERROR: the attendance payload did not include a "
                f"calendar, so the run could not be verified. final_url={safe_page_url(page)}",
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
                f"the saved session is no longer valid. response_status={post_response.status} "
                f"final_url={safe_page_url(page)}",
                SESSION_EXPIRED,
            )
        post_seen = post_response.ok
        attendance_payload, refreshed_state = refresh_attendance_payload_with_retries(
            page=page,
            attendance_path=attendance_path,
            timeout_ms=timeout_ms,
        )

        if refreshed_state.status == UNKNOWN and page_looks_logged_out(page):
            return (
                "SESSION_EXPIRED: the sign-in page no longer looks logged in after the "
                f"sign-in click. final_url={safe_page_url(page)}",
                SESSION_EXPIRED,
            )

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
                f"page appears to be logged out. final_url={safe_page_url(page)}",
                SESSION_EXPIRED,
            )
        return (
            "ERROR: timed out while waiting for attendance responses from the page. "
            f"final_url={safe_page_url(page)}",
            ERROR,
        )
    finally:
        close_page = getattr(page, "close", None)
        if callable(close_page):
            try:
                close_page()
            except Exception:
                pass


def refresh_attendance_payload_with_retries(
    *,
    page,
    attendance_path: str,
    timeout_ms: int,
):
    from playwright.sync_api import Error as PlaywrightError
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    attendance_payload = {"code": -1, "data": {"calendar": []}}
    refreshed_state = derive_attendance_state(attendance_payload)

    for attempt in range(REFRESH_VERIFICATION_ATTEMPTS):
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
        except (ValueError, TypeError, PlaywrightError):
            attendance_payload = {"code": -1, "data": {"calendar": []}}
        try:
            page.wait_for_timeout(2000)
        except PlaywrightTimeoutError:
            pass
        refreshed_state = derive_attendance_state(attendance_payload)
        if refreshed_state.status == ALREADY_DONE:
            break
        if attempt + 1 < REFRESH_VERIFICATION_ATTEMPTS:
            try:
                page.wait_for_timeout(REFRESH_VERIFICATION_DELAY_MS)
            except PlaywrightTimeoutError:
                pass

    return attendance_payload, refreshed_state


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
    return page_has_login_form(page)


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


def safe_page_url(page) -> str:
    try:
        return str(page.url)
    except Exception:
        return "<unavailable>"

def prefix_site_message(site: SiteSettings, message: str) -> str:
    return f"[{site.name}] {message}"


def site_log_details(*, site: SiteSettings, profile_dir: Path) -> dict[str, str]:
    return {
        "site_key": site.key,
        "profile_dir": str(profile_dir),
        "signin_url": site.signin_url,
        "attendance_path": site.attendance_path,
    }


def write_log(
    log_dir: Path,
    now: datetime,
    status: str,
    message: str,
    *,
    details: dict[str, str] | None = None,
) -> None:
    log_file = log_dir / f"signin-{now.date().isoformat()}.log"
    detail_text = ""
    if details:
        detail_text = "".join(f" | {key}={value}" for key, value in details.items())
    entry = f"[{now.isoformat()}] {status} {message}{detail_text}\n"
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
