import io
import json
import tempfile
import unittest
from argparse import Namespace
from contextlib import redirect_stderr, redirect_stdout
from datetime import timezone
from pathlib import Path
from unittest.mock import patch

from skport_signin.commands import run as sign_in
from skport_signin.errors import InteractionError, StateFileError
from skport_signin.runtime import build_runtime_context
from skport_signin.statuses import SUCCESS


class _FakeResponse:
    def __init__(
        self,
        status: int,
        payload: dict | None = None,
        ok: bool = True,
        *,
        method: str = "GET",
        url: str = "https://zonai.skport.com/web/v1/game/endfield/attendance",
    ) -> None:
        self.status = status
        self._payload = payload or {}
        self.ok = ok
        self.url = url
        self.request = type("Request", (), {"method": method})()

    def json(self) -> dict:
        return self._payload


class _FakeExpectResponse:
    def __init__(self, response: _FakeResponse) -> None:
        self.value = response

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class _BodyLocator:
    def __init__(self, text: str) -> None:
        self._text = text

    def inner_text(self, timeout: int = 2000) -> str:
        return self._text


class _CountLocator:
    def __init__(self, count: int) -> None:
        self._count = count

    def count(self) -> int:
        return self._count


class _ClickableLocator:
    def __init__(
        self,
        name: str,
        *,
        success: bool = False,
        children: dict[str, "_ClickableLocator"] | None = None,
    ) -> None:
        self.name = name
        self.success = success
        self.children = children or {}
        self.clicked = False

    @property
    def first(self):
        return self

    def locator(self, selector: str):
        return self.children.get(
            selector,
            _ClickableLocator(f"{self.name}->{selector}", success=False),
        )

    def scroll_into_view_if_needed(self, timeout: int = 2000) -> None:
        return None

    def click(self, timeout: int = 2000, force: bool = True) -> None:
        if not self.success:
            raise RuntimeError(f"{self.name} was not clickable")
        self.clicked = True


class _FakePage:
    def __init__(self, responses: list[_FakeResponse]) -> None:
        self._responses = list(responses)
        self.url = "https://game.skport.com/endfield/sign-in"
        self.body_text = ""
        self.login_form_count = 0

    def set_default_timeout(self, timeout_ms: int) -> None:
        return None

    def expect_response(self, predicate, timeout: int):
        for index, response in enumerate(self._responses):
            if predicate(response):
                self._responses.pop(index)
                return _FakeExpectResponse(response)
        raise AssertionError("No queued response matched the expected predicate")

    def goto(self, url: str, wait_until: str) -> None:
        return None

    def wait_for_timeout(self, timeout_ms: int) -> None:
        return None

    def reload(self, wait_until: str) -> None:
        return None

    def close(self) -> None:
        return None

    def locator(self, selector: str):
        if selector == "body":
            return _BodyLocator(self.body_text)
        if "password" in selector:
            return _CountLocator(self.login_form_count)
        raise AssertionError("click_day_tile should be mocked in this test")

    def get_by_text(self, text: str, exact: bool = False):
        raise AssertionError("click_day_tile should be mocked in this test")


class _ClickPage:
    def __init__(
        self,
        *,
        locators: dict[str, _ClickableLocator] | None = None,
        texts: dict[str, _ClickableLocator] | None = None,
    ) -> None:
        self._locators = locators or {}
        self._texts = texts or {}

    def locator(self, selector: str):
        return self._locators.get(selector, _ClickableLocator(selector, success=False))

    def get_by_text(self, text: str, exact: bool = False):
        return self._texts.get(text, _ClickableLocator(text, success=False))


class _FakeContext:
    def __init__(self, page: _FakePage | list[_FakePage]) -> None:
        self.pages = []
        if isinstance(page, list):
            self._pages = list(page)
        else:
            self._pages = [page]

    def new_page(self) -> _FakePage:
        if not self._pages:
            raise AssertionError("No queued fake pages remain")
        page = self._pages.pop(0)
        self.pages.append(page)
        return page

    def close(self) -> None:
        return None


class _FakeChromium:
    def __init__(self, context: _FakeContext) -> None:
        self._context = context
        self.launch_count = 0
        self.executable_path = "C:/fake/chromium.exe"

    def launch_persistent_context(self, *args, **kwargs) -> _FakeContext:
        self.launch_count += 1
        return self._context


class _FakePlaywright:
    def __init__(self, context: _FakeContext) -> None:
        self.chromium = _FakeChromium(context)


class _FakeSyncPlaywright:
    def __init__(self, playwright) -> None:
        self._playwright = playwright

    def __enter__(self):
        return self._playwright

    def __exit__(self, exc_type, exc, tb) -> bool:
        return False


class SignInTests(unittest.TestCase):
    def test_run_browser_sign_in_returns_message_then_status_on_success(self) -> None:
        attendance_payload = {
            "data": {
                "calendar": [
                    {"available": True, "done": False},
                    {"available": False, "done": False},
                ]
            }
        }
        refreshed_payload = {
            "data": {
                "calendar": [
                    {"available": False, "done": True},
                    {"available": False, "done": False},
                ]
            }
        }
        fake_page = _FakePage(
            [
                _FakeResponse(200, attendance_payload, method="GET"),
                _FakeResponse(200, {}, ok=True, method="POST"),
                _FakeResponse(200, refreshed_payload, method="GET"),
            ]
        )
        fake_context = _FakeContext(fake_page)

        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "browser-profile"
            profile_dir.mkdir()
            with patch.object(sign_in, "click_day_tile"), patch(
                "playwright.sync_api.sync_playwright",
                return_value=_FakeSyncPlaywright(_FakePlaywright(fake_context)),
            ):
                message, status = sign_in.run_browser_sign_in(
                    profile_dir=profile_dir,
                    signin_url="https://example.com",
                    attendance_path="/web/v1/game/endfield/attendance",
                    headless=True,
                    browser_channel="",
                    timeout_seconds=1,
                )

        self.assertEqual(status, SUCCESS)
        self.assertIn("Day 1", message)

    def test_run_browser_sign_in_retries_refreshed_state_after_successful_post(self) -> None:
        attendance_payload = {
            "data": {
                "calendar": [
                    {"available": True, "done": False},
                    {"available": False, "done": False},
                ]
            }
        }
        unknown_refresh_payload = {"data": {}}
        refreshed_payload = {
            "data": {
                "calendar": [
                    {"available": False, "done": True},
                    {"available": False, "done": False},
                ]
            }
        }
        fake_page = _FakePage(
            [
                _FakeResponse(200, attendance_payload, method="GET"),
                _FakeResponse(200, {}, ok=True, method="POST"),
                _FakeResponse(200, unknown_refresh_payload, method="GET"),
                _FakeResponse(200, refreshed_payload, method="GET"),
            ]
        )
        fake_context = _FakeContext(fake_page)

        with tempfile.TemporaryDirectory() as temp_dir:
            profile_dir = Path(temp_dir) / "browser-profile"
            profile_dir.mkdir()
            with patch.object(sign_in, "click_day_tile"), patch(
                "playwright.sync_api.sync_playwright",
                return_value=_FakeSyncPlaywright(_FakePlaywright(fake_context)),
            ):
                message, status = sign_in.run_browser_sign_in(
                    profile_dir=profile_dir,
                    signin_url="https://example.com",
                    attendance_path="/web/v1/game/endfield/attendance",
                    headless=True,
                    browser_channel="",
                    timeout_seconds=1,
                )

        self.assertEqual(status, SUCCESS)
        self.assertIn("Day 1", message)

    def test_main_dry_run_reports_each_enabled_site(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "log_dir": "./logs",
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "attendance_path": "/web/v1/game/endfield/attendance",
                                "state_path": "./endfield-state.json",
                                "browser_profile_dir": "./endfield-profile",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "attendance_path": "/api/v1/game/attendance",
                                "state_path": "./arknights-state.json",
                                "browser_profile_dir": "./arknights-profile",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=True, force=False),
            ), patch.object(
                sign_in,
                "load_timezone",
                return_value=timezone.utc,
            ), redirect_stdout(stdout):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 0)
        output = stdout.getvalue()
        self.assertIn("[Endfield] Dry run only.", output)
        self.assertIn("[Arknights] Dry run only.", output)

    def test_main_uses_per_site_state_and_attendance_paths(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "attendance_path": "/web/v1/game/endfield/attendance",
                                "state_path": "./endfield-state.json",
                                "browser_profile_dir": "./endfield-profile",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "attendance_path": "/api/v1/game/attendance",
                                "state_path": "./arknights-state.json",
                                "browser_profile_dir": "./arknights-profile",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            captured_state_paths = []
            captured_attendance_paths = []

            original_mark_attempt = sign_in.mark_attempt

            def fake_mark_attempt(path, state):
                captured_state_paths.append(path.name)
                original_mark_attempt(path, state)

            def fake_run_browser_sign_in(**kwargs):
                captured_attendance_paths.append(kwargs["attendance_path"])
                return "SUCCESS: mocked.", SUCCESS

            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=False, force=True),
            ), patch.object(sign_in, "load_timezone", return_value=timezone.utc), patch.object(
                sign_in,
                "mark_attempt",
                side_effect=fake_mark_attempt,
            ), patch.object(
                sign_in,
                "run_browser_sign_in",
                side_effect=fake_run_browser_sign_in,
            ), patch.object(
                sign_in,
                "notify_status",
                return_value=None,
            ):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(captured_state_paths, ["endfield-state.json", "arknights-state.json"])
        self.assertEqual(
            captured_attendance_paths,
            ["/web/v1/game/endfield/attendance", "/api/v1/game/attendance"],
        )

    def test_main_shared_profile_uses_single_browser_context(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            profile_dir = root / "shared-profile"
            profile_dir.mkdir()
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "attendance_path": "/web/v1/game/endfield/attendance",
                                "state_path": "./endfield-state.json",
                                "browser_profile_dir": "./shared-profile",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "attendance_path": "/api/v1/game/attendance",
                                "state_path": "./arknights-state.json",
                                "browser_profile_dir": "./shared-profile",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            endfield_page = _FakePage(
                [
                    _FakeResponse(
                        200,
                        {
                            "data": {
                                "calendar": [
                                    {"available": True, "done": False},
                                    {"available": False, "done": False},
                                ]
                            }
                        },
                        method="GET",
                        url="https://game.skport.com/web/v1/game/endfield/attendance",
                    ),
                    _FakeResponse(
                        200,
                        {},
                        ok=True,
                        method="POST",
                        url="https://game.skport.com/web/v1/game/endfield/attendance",
                    ),
                    _FakeResponse(
                        200,
                        {
                            "data": {
                                "calendar": [
                                    {"available": False, "done": True},
                                    {"available": False, "done": False},
                                ]
                            }
                        },
                        method="GET",
                        url="https://game.skport.com/web/v1/game/endfield/attendance",
                    ),
                ]
            )
            arknights_page = _FakePage(
                [
                    _FakeResponse(
                        200,
                        {
                            "data": {
                                "calendar": [
                                    {"available": True, "done": False},
                                    {"available": False, "done": False},
                                ]
                            }
                        },
                        method="GET",
                        url="https://game.skport.com/api/v1/game/attendance",
                    ),
                    _FakeResponse(
                        200,
                        {},
                        ok=True,
                        method="POST",
                        url="https://game.skport.com/api/v1/game/attendance",
                    ),
                    _FakeResponse(
                        200,
                        {
                            "data": {
                                "calendar": [
                                    {"available": False, "done": True},
                                    {"available": False, "done": False},
                                ]
                            }
                        },
                        method="GET",
                        url="https://game.skport.com/api/v1/game/attendance",
                    ),
                ]
            )
            fake_context = _FakeContext([endfield_page, arknights_page])
            fake_playwright = _FakePlaywright(fake_context)

            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=False, force=True),
            ), patch.object(sign_in, "load_timezone", return_value=timezone.utc), patch.object(
                sign_in,
                "click_day_tile",
            ), patch.object(
                sign_in,
                "notify_status",
                return_value=None,
            ), patch.object(
                sign_in,
                "ensure_browser_runtime_available",
            ), patch(
                "playwright.sync_api.sync_playwright",
                return_value=_FakeSyncPlaywright(fake_playwright),
            ):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 0)
        self.assertEqual(fake_playwright.chromium.launch_count, 1)

    def test_main_reports_state_file_errors_separately(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "timezone": "Asia/Taipei",
                        "state_path": "./state.json",
                        "log_dir": "./logs",
                        "browser_profile_dir": "./browser-profile",
                    }
                ),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=False, force=False),
            ), patch.object(sign_in, "load_timezone", return_value=timezone.utc), patch.object(
                sign_in, "should_run_today", side_effect=StateFileError("broken state")
            ), redirect_stderr(stderr):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 30)
        self.assertIn("State file error", stderr.getvalue())

    def test_main_reports_timezone_errors_as_configuration_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "timezone": "Asia/Taipei",
                        "state_path": "./state.json",
                        "log_dir": "./logs",
                        "browser_profile_dir": "./browser-profile",
                    }
                ),
                encoding="utf-8",
            )
            stderr = io.StringIO()
            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=False, force=False),
            ), patch.object(
                sign_in,
                "load_timezone",
                side_effect=RuntimeError("bad timezone"),
            ), redirect_stderr(stderr):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 30)
        self.assertIn("Configuration error", stderr.getvalue())

    def test_main_reports_interaction_errors_as_runtime_errors(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "timezone": "Asia/Taipei",
                        "state_path": "./state.json",
                        "log_dir": "./logs",
                        "browser_profile_dir": "./browser-profile",
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()
            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=False, force=True),
            ), patch.object(sign_in, "load_timezone", return_value=timezone.utc), patch.object(
                sign_in,
                "run_browser_sign_in",
                side_effect=InteractionError("could not click tile"),
            ), redirect_stdout(stdout):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 10)
        self.assertIn(
            "ERROR: unhandled runtime exception during sign-in attempt: could not click tile",
            stdout.getvalue(),
        )

    def test_main_continues_after_site_runtime_exception(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "attendance_path": "/web/v1/game/endfield/attendance",
                                "state_path": "./endfield-state.json",
                                "browser_profile_dir": "./endfield-profile",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "attendance_path": "/api/v1/game/attendance",
                                "state_path": "./arknights-state.json",
                                "browser_profile_dir": "./arknights-profile",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )
            stdout = io.StringIO()

            def fake_run_browser_sign_in(**kwargs):
                if kwargs["attendance_path"] == "/web/v1/game/endfield/attendance":
                    raise RuntimeError("boom")
                return "SUCCESS: mocked.", SUCCESS

            with patch.object(
                sign_in,
                "parse_args",
                return_value=Namespace(config=str(config_path), dry_run=False, force=True),
            ), patch.object(sign_in, "load_timezone", return_value=timezone.utc), patch.object(
                sign_in,
                "run_browser_sign_in",
                side_effect=fake_run_browser_sign_in,
            ), patch.object(
                sign_in,
                "notify_status",
                return_value=None,
            ), redirect_stdout(stdout):
                exit_code = sign_in.main()

        self.assertEqual(exit_code, 10)
        output = stdout.getvalue()
        self.assertIn(
            "[Endfield] ERROR: unhandled runtime exception during sign-in attempt: boom",
            output,
        )
        self.assertIn("[Arknights] SUCCESS: mocked.", output)

    def test_run_command_keeps_running_when_console_streams_are_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config_path = root / "settings.json"
            config_path.write_text(
                json.dumps(
                    {
                        "sites": [
                            {
                                "key": "endfield",
                                "name": "Endfield",
                                "signin_url": "https://game.skport.com/endfield/sign-in",
                                "attendance_path": "/web/v1/game/endfield/attendance",
                                "state_path": "./endfield-state.json",
                                "browser_profile_dir": "./endfield-profile",
                            },
                            {
                                "key": "arknights",
                                "name": "Arknights",
                                "signin_url": "https://game.skport.com/arknights/sign-in",
                                "attendance_path": "/api/v1/game/attendance",
                                "state_path": "./arknights-state.json",
                                "browser_profile_dir": "./arknights-profile",
                            },
                        ]
                    }
                ),
                encoding="utf-8",
            )

            with patch("skport_signin.runtime.sys.stdout", None), patch(
                "skport_signin.runtime.sys.stderr",
                None,
            ):
                runtime = build_runtime_context(config_override=str(config_path))

            with patch.object(sign_in, "load_timezone", return_value=timezone.utc), patch.object(
                sign_in,
                "run_browser_sign_in",
                return_value=("SUCCESS: mocked.", SUCCESS),
            ), patch.object(
                sign_in,
                "notify_status",
                return_value=None,
            ):
                exit_code = sign_in.run_command(runtime=runtime, dry_run=False, force=True)

            endfield_state = json.loads(
                (root / "endfield-state.json").read_text(encoding="utf-8")
            )
            arknights_state = json.loads(
                (root / "arknights-state.json").read_text(encoding="utf-8")
            )
            self.assertEqual(exit_code, 0)
            self.assertEqual(endfield_state["last_status"], SUCCESS)
            self.assertEqual(arknights_state["last_status"], SUCCESS)

    def test_page_looks_logged_out_does_not_treat_account_text_as_login(self) -> None:
        page = _FakePage([])
        page.body_text = "Open account settings"
        page.login_form_count = 0

        self.assertFalse(sign_in.page_looks_logged_out(page))

    def test_page_looks_logged_out_does_not_treat_sign_in_copy_as_login(self) -> None:
        page = _FakePage([])
        page.body_text = "Sign in every day to claim today's reward"
        page.login_form_count = 0

        self.assertFalse(sign_in.page_looks_logged_out(page))

    def test_page_looks_logged_out_for_login_url(self) -> None:
        page = _FakePage([])
        page.url = "https://example.com/login"

        self.assertTrue(sign_in.page_looks_logged_out(page))

    def test_page_looks_logged_out_for_login_form(self) -> None:
        page = _FakePage([])
        page.login_form_count = 1

        self.assertTrue(sign_in.page_looks_logged_out(page))

    def test_click_day_tile_prefers_card_actionable_descendant(self) -> None:
        button = _ClickableLocator("card-button", success=True)
        container = _ClickableLocator(
            "card-container",
            success=False,
            children={sign_in.ACTIONABLE_DESCENDANT_SELECTOR: button},
        )
        page = _ClickPage(locators={"card-selector": container})

        with patch.object(
            sign_in,
            "day_card_selector_candidates",
            return_value=["card-selector"],
        ), patch.object(sign_in, "day_label_candidates", return_value=["Day 9"]):
            sign_in.click_day_tile(page, 9)

        self.assertTrue(button.clicked)

    def test_click_day_tile_falls_back_to_text_match(self) -> None:
        text_locator = _ClickableLocator("text-match", success=True)
        failing_container = _ClickableLocator("card-container", success=False)
        page = _ClickPage(
            locators={
                "card-selector": failing_container,
                "text=Day 9": _ClickableLocator("text-selector", success=False),
                "div:has-text('Day 9')": _ClickableLocator("div-text-selector", success=False),
            },
            texts={"Day 9": text_locator},
        )

        with patch.object(
            sign_in,
            "day_card_selector_candidates",
            return_value=["card-selector"],
        ), patch.object(sign_in, "day_label_candidates", return_value=["Day 9"]):
            sign_in.click_day_tile(page, 9)

        self.assertTrue(text_locator.clicked)

    def test_missing_profile_error_references_unified_cli(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_profile = Path(temp_dir) / "nonexistent-profile"
            with self.assertRaises(FileNotFoundError) as cm:
                sign_in.run_browser_sign_in(
                    profile_dir=missing_profile,
                    signin_url="https://example.com",
                    attendance_path="/web/v1/game/endfield/attendance",
                    headless=True,
                    browser_channel="",
                    timeout_seconds=1,
                )
            self.assertIn("skport_signin capture-session", str(cm.exception))
            self.assertNotIn("capture_session.py", str(cm.exception))


if __name__ == "__main__":
    unittest.main()
