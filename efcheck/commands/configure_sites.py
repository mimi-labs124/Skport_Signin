from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from efcheck.default_settings import build_default_settings, known_site_keys
from efcheck.errors import ConfigError
from efcheck.runtime import RuntimeContext, build_runtime_context


def register_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "configure-sites",
        help="Rewrite the configured sites in settings.json.",
    )
    parser.add_argument(
        "--enable-site",
        action="append",
        default=[],
        metavar="SITE",
        help="Enable a known site key. Repeat for multiple sites.",
    )
    parser.add_argument(
        "--disable-site",
        action="append",
        default=[],
        metavar="SITE",
        help="Disable a known site key. Repeat for multiple sites.",
    )
    parser.add_argument(
        "--share-arknights-profile",
        action="store_true",
        help="Share the Endfield browser profile with Arknights.",
    )
    parser.set_defaults(handler=handle_command)


def handle_command(args, runtime: RuntimeContext) -> int:
    configure_sites(
        runtime.app_paths.config_file,
        runtime=runtime,
        enabled_sites=resolve_enabled_sites(
            runtime.app_paths.config_file,
            enable_sites=args.enable_site,
            disable_sites=args.disable_site,
        ),
        share_profile_with_arknights=args.share_arknights_profile,
    )
    runtime.stdout.write(f"Configured sites in {runtime.app_paths.config_file}\n")
    return 0


def configure_sites(
    config_path: Path,
    *,
    runtime: RuntimeContext | None = None,
    enabled_sites: set[str] | None,
    share_profile_with_arknights: bool,
) -> None:
    runtime = runtime or build_runtime_context(config_override=str(config_path))
    data = _load_existing_config(config_path)
    defaults = build_default_settings(
        runtime.app_paths,
        enabled_sites=enabled_sites,
        share_profile_with_arknights=share_profile_with_arknights,
    )
    data["sites"] = defaults["sites"]

    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(data, ensure_ascii=True, indent=2) + "\n", encoding="utf-8")


def _load_existing_config(config_path: Path) -> dict:
    if not config_path.exists():
        return {}

    data = json.loads(config_path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Configuration file at {config_path} must contain a JSON object.")
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
        }
    }


def resolve_enabled_sites(
    config_path: Path,
    *,
    enable_sites: list[str],
    disable_sites: list[str],
) -> set[str]:
    known = set(known_site_keys())
    requested_enable = {site.strip().casefold() for site in enable_sites if site.strip()}
    requested_disable = {site.strip().casefold() for site in disable_sites if site.strip()}
    unknown = (requested_enable | requested_disable) - known
    if unknown:
        known_sites_text = ", ".join(sorted(known))
        unknown_sites_text = ", ".join(sorted(unknown))
        raise ConfigError(
            f"Unknown site key(s): {unknown_sites_text}. Known sites: {known_sites_text}."
        )

    if requested_enable & requested_disable:
        overlap = ", ".join(sorted(requested_enable & requested_disable))
        raise ConfigError(f"Site key(s) cannot be both enabled and disabled: {overlap}.")

    enabled_sites = existing_enabled_sites(config_path)
    enabled_sites.update(requested_enable)
    enabled_sites.difference_update(requested_disable)
    if not enabled_sites:
        raise ConfigError("At least one site must be enabled.")
    return enabled_sites


def existing_enabled_sites(config_path: Path) -> set[str]:
    if not config_path.exists():
        return {"endfield"}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"endfield"}
    if not isinstance(data, dict):
        return {"endfield"}

    sites = data.get("sites")
    if not isinstance(sites, list):
        return {"endfield"}

    enabled = set()
    for site in sites:
        if not isinstance(site, dict):
            continue
        key = site.get("key")
        if isinstance(key, str) and site.get("enabled", True) is True:
            enabled.add(key.strip().casefold())
    return enabled or {"endfield"}


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Configure EFCheck sites for guided setup.")
    parser.add_argument("--config", default="config/settings.json", help="Path to settings.json")
    parser.add_argument(
        "--enable-site",
        action="append",
        default=[],
        help="Enable a known site key.",
    )
    parser.add_argument(
        "--disable-site",
        action="append",
        default=[],
        help="Disable a known site key.",
    )
    parser.add_argument(
        "--include-arknights",
        action="store_true",
        help=argparse.SUPPRESS,
    )
    parser.add_argument(
        "--share-arknights-profile",
        action="store_true",
        help="Use the same browser profile directory for Endfield and Arknights.",
    )
    return parser.parse_args(argv)


def legacy_main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    runtime = build_runtime_context(config_override=args.config)
    try:
        enable_sites = list(args.enable_site)
        if args.include_arknights and "arknights" not in [site.casefold() for site in enable_sites]:
            enable_sites.append("arknights")
        configure_sites(
            runtime.app_paths.config_file,
            runtime=runtime,
            enabled_sites=resolve_enabled_sites(
                runtime.app_paths.config_file,
                enable_sites=enable_sites,
                disable_sites=args.disable_site,
            ),
            share_profile_with_arknights=args.share_arknights_profile,
        )
    except FileNotFoundError as exc:
        print(f"Missing file: {exc}", file=sys.stderr)
        return 30
    except (ConfigError, ValueError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 30

    print("Configured EFCheck sites.")
    return 0


main = legacy_main
