from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse

from efcheck.default_settings import (
    ARKNIGHTS_KEY,
    ENDFIELD_KEY,
    KNOWN_SITES,
)
from efcheck.errors import ConfigError

DEFAULT_TIMEZONE = "Asia/Taipei"
DEFAULT_STATE_PATH = "../state/last_run.json"
DEFAULT_LOG_DIR = "../logs"
DEFAULT_BROWSER_PROFILE_DIR = "../state/browser-profile"
DEFAULT_BROWSER_CHANNEL = ""
DEFAULT_HEADLESS = True
DEFAULT_TIMEOUT_SECONDS = 20
KNOWN_ATTENDANCE_PATHS = {
    ARKNIGHTS_KEY: "/api/v1/game/attendance",
}
DEFAULT_ENDFIELD_KEY = ENDFIELD_KEY


@dataclass(frozen=True)
class SiteSettings:
    key: str
    name: str
    signin_url: str
    attendance_path: str
    state_path: str
    browser_profile_dir: str
    enabled: bool


@dataclass(frozen=True)
class RuntimeSettings:
    timezone: str
    log_dir: str
    browser_channel: str
    headless: bool
    timeout_seconds: int
    sites: tuple[SiteSettings, ...]


def load_runtime_settings(config_path: Path, default_url: str) -> RuntimeSettings:
    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Could not parse config file at {config_path}: {exc.msg}.") from exc

    if not isinstance(data, dict):
        raise ConfigError(f"Configuration file at {config_path} must contain a JSON object.")

    sites = _parse_sites(data, default_url)
    if not any(site.enabled for site in sites):
        raise ConfigError("At least one site must be enabled.")

    return RuntimeSettings(
        timezone=_parse_string(data.get("timezone", DEFAULT_TIMEZONE), field_name="timezone"),
        log_dir=_parse_string(data.get("log_dir", DEFAULT_LOG_DIR), field_name="log_dir"),
        browser_channel=_parse_string(
            data.get("browser_channel", DEFAULT_BROWSER_CHANNEL),
            field_name="browser_channel",
        ),
        headless=_parse_bool(data.get("headless", DEFAULT_HEADLESS), field_name="headless"),
        timeout_seconds=_parse_int(
            data.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            field_name="timeout_seconds",
            minimum=1,
        ),
        sites=tuple(sites),
    )


def resolve_path(config_path: Path, raw_path: str) -> Path:
    candidate = Path(raw_path)
    if candidate.is_absolute():
        return candidate
    return (config_path.parent / candidate).resolve()


def find_site(settings: RuntimeSettings, selected_site: str | None) -> SiteSettings:
    key = (selected_site or ENDFIELD_KEY).strip().casefold()
    for site in settings.sites:
        if site.key.casefold() == key or site.name.casefold() == key:
            return site
    available_sites = ", ".join(site.key for site in settings.sites)
    raise ConfigError(
        f"Unknown site '{selected_site}'. Available sites: {available_sites}."
    )


def _parse_sites(data: dict, default_url: str) -> list[SiteSettings]:
    sites_data = data.get("sites")
    if sites_data is None:
        signin_url = _parse_string(data.get("signin_url", default_url), field_name="signin_url")
        return [
            SiteSettings(
                key=ENDFIELD_KEY,
                name=next(site.name for site in KNOWN_SITES if site.key == ENDFIELD_KEY),
                signin_url=signin_url,
                attendance_path=_parse_string(
                    data.get("attendance_path", derive_attendance_path(signin_url)),
                    field_name="attendance_path",
                ),
                state_path=_parse_string(
                    data.get("state_path", DEFAULT_STATE_PATH),
                    field_name="state_path",
                ),
                browser_profile_dir=_parse_string(
                    data.get("browser_profile_dir", DEFAULT_BROWSER_PROFILE_DIR),
                    field_name="browser_profile_dir",
                ),
                enabled=True,
            )
        ]

    if not isinstance(sites_data, list) or not sites_data:
        raise ConfigError("'sites' must be a non-empty JSON array.")

    sites: list[SiteSettings] = []
    seen_keys: set[str] = set()
    for index, raw_site in enumerate(sites_data):
        field_prefix = f"sites[{index}]"
        if not isinstance(raw_site, dict):
            raise ConfigError(f"{field_prefix} must be an object, not {raw_site!r}.")

        signin_url = _parse_string(
            raw_site.get("signin_url"),
            field_name=f"{field_prefix}.signin_url",
        )
        derived_key = normalize_site_key(raw_site.get("key"), signin_url)
        if derived_key in seen_keys:
            raise ConfigError(f"Duplicate site key '{derived_key}' in {field_prefix}.")
        seen_keys.add(derived_key)

        name = _parse_string(
            raw_site.get("name", derived_key.title()),
            field_name=f"{field_prefix}.name",
        )
        browser_profile_dir = _parse_string(
            raw_site.get("browser_profile_dir", DEFAULT_BROWSER_PROFILE_DIR),
            field_name=f"{field_prefix}.browser_profile_dir",
        )
        state_path = _parse_string(
            raw_site.get("state_path", f"../state/{derived_key}-last_run.json"),
            field_name=f"{field_prefix}.state_path",
        )
        attendance_path = _parse_string(
            raw_site.get("attendance_path", derive_attendance_path(signin_url)),
            field_name=f"{field_prefix}.attendance_path",
        )
        enabled = _parse_bool(raw_site.get("enabled", True), field_name=f"{field_prefix}.enabled")

        sites.append(
            SiteSettings(
                key=derived_key,
                name=name,
                signin_url=signin_url,
                attendance_path=attendance_path,
                state_path=state_path,
                browser_profile_dir=browser_profile_dir,
                enabled=enabled,
            )
        )

    return sites


def derive_attendance_path(signin_url: str) -> str:
    slug = derive_site_slug(signin_url)
    if slug in KNOWN_ATTENDANCE_PATHS:
        return KNOWN_ATTENDANCE_PATHS[slug]
    return f"/web/v1/game/{slug}/attendance"


def normalize_site_key(raw_value: object, signin_url: str) -> str:
    if raw_value is None:
        return derive_site_slug(signin_url)
    key = _parse_string(raw_value, field_name="site.key").strip().casefold()
    if not key:
        raise ConfigError("site.key must not be empty.")
    return key


def derive_site_slug(signin_url: str) -> str:
    path = urlparse(signin_url).path.rstrip("/")
    match = re.fullmatch(r"/(?P<slug>[^/]+)/sign-in", path)
    if not match:
        raise ConfigError(f"Could not derive site key from signin_url {signin_url!r}.")
    return match.group("slug")


def _parse_string(value: object, *, field_name: str) -> str:
    if isinstance(value, str):
        return value
    raise ConfigError(f"{field_name} must be a string, not {value!r}.")


def _parse_bool(value: object, *, field_name: str) -> bool:
    if isinstance(value, bool):
        return value
    raise ConfigError(f"{field_name} must be true or false, not {value!r}.")


def _parse_int(value: object, *, field_name: str, minimum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ConfigError(f"{field_name} must be an integer, not {value!r}.")
    if minimum is not None and value < minimum:
        raise ConfigError(f"{field_name} must be >= {minimum}, not {value!r}.")
    return value
