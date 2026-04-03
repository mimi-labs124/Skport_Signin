from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from skport_signin.app_paths import AppPaths
from skport_signin.file_io import write_text_atomic

ENDFIELD_KEY = "endfield"
ARKNIGHTS_KEY = "arknights"


@dataclass(frozen=True)
class KnownSite:
    key: str
    name: str
    signin_url: str
    attendance_path: str


KNOWN_SITES: tuple[KnownSite, ...] = (
    KnownSite(
        key=ENDFIELD_KEY,
        name="Endfield",
        signin_url="https://game.skport.com/endfield/sign-in?header=0&hg_media=skport&hg_link_campaign=tools",
        attendance_path="/web/v1/game/endfield/attendance",
    ),
    KnownSite(
        key=ARKNIGHTS_KEY,
        name="Arknights",
        signin_url="https://game.skport.com/arknights/sign-in",
        attendance_path="/api/v1/game/attendance",
    ),
)

DEFAULT_ENABLED_SITES = frozenset({ENDFIELD_KEY})


def build_default_settings(
    paths: AppPaths,
    *,
    enabled_sites: set[str] | frozenset[str] | None = None,
    share_profile_with_arknights: bool = False,
) -> dict:
    enabled_keys = normalize_enabled_sites(enabled_sites)
    settings = {
        "timezone": "Asia/Taipei",
        "log_dir": "../logs",
        "browser_channel": "",
        "headless": True,
        "timeout_seconds": 20,
        "sites": [
            build_site_entry(
                paths,
                site,
                enabled=site.key in enabled_keys,
                share_profile_with_arknights=share_profile_with_arknights,
            )
            for site in KNOWN_SITES
        ],
    }
    return settings


def write_default_settings(
    paths: AppPaths,
    *,
    config_path: Path | None = None,
    enabled_sites: set[str] | frozenset[str] | None = None,
    share_profile_with_arknights: bool = False,
    force: bool = False,
) -> Path:
    target_path = config_path or paths.config_file
    if target_path.exists() and not force:
        return target_path

    target_path.parent.mkdir(parents=True, exist_ok=True)
    write_text_atomic(
        target_path,
        json.dumps(
            build_default_settings(
                paths,
                enabled_sites=enabled_sites,
                share_profile_with_arknights=share_profile_with_arknights,
            ),
            ensure_ascii=True,
            indent=2,
        ) + "\n",
        encoding="utf-8",
    )
    return target_path


def known_site_keys() -> tuple[str, ...]:
    return tuple(site.key for site in KNOWN_SITES)


def normalize_enabled_sites(
    enabled_sites: set[str] | frozenset[str] | None,
) -> frozenset[str]:
    if enabled_sites is None:
        return DEFAULT_ENABLED_SITES

    return frozenset(site.strip().casefold() for site in enabled_sites if site.strip())


def build_site_entry(
    paths: AppPaths,
    site: KnownSite,
    *,
    enabled: bool,
    share_profile_with_arknights: bool,
) -> dict:
    return {
        "key": site.key,
        "name": site.name,
        "enabled": enabled,
        "signin_url": site.signin_url,
        "attendance_path": site.attendance_path,
        "state_path": default_state_path(site.key),
        "browser_profile_dir": default_profile_dir(
            paths,
            site.key,
            enabled=enabled,
            share_profile_with_arknights=share_profile_with_arknights,
        ),
    }


def default_state_path(site_key: str) -> str:
    return f"../state/{site_key}-last_run.json"


def default_profile_dir(
    paths: AppPaths,
    site_key: str,
    *,
    enabled: bool,
    share_profile_with_arknights: bool,
) -> str:
    if site_key == ENDFIELD_KEY:
        if paths.mode == "packaged":
            return "../browser-profile/endfield"
        return "../state/browser-profile"

    if site_key == ARKNIGHTS_KEY and enabled and share_profile_with_arknights:
        return default_profile_dir(
            paths,
            ENDFIELD_KEY,
            enabled=True,
            share_profile_with_arknights=False,
        )

    if paths.mode == "packaged":
        return f"../browser-profile/{site_key}"
    return f"../state/{site_key}-browser-profile"

