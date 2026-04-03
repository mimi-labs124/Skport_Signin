from __future__ import annotations

from efcheck.commands.configure_sites import resolve_enabled_sites
from efcheck.default_settings import write_default_settings
from efcheck.runtime import RuntimeContext


def register_parser(subparsers) -> None:
    parser = subparsers.add_parser(
        "init",
        help="Create the local EFCheck config file if it does not exist.",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing settings.json file.",
    )
    parser.add_argument(
        "--enable-site",
        action="append",
        default=[],
        help="Enable a known site key in the initialized config.",
    )
    parser.add_argument(
        "--disable-site",
        action="append",
        default=[],
        help="Disable a known site key in the initialized config.",
    )
    parser.add_argument(
        "--share-arknights-profile",
        action="store_true",
        help="Use the same browser profile path for Endfield and Arknights.",
    )
    parser.set_defaults(handler=handle_command)


def handle_command(args, runtime: RuntimeContext) -> int:
    enabled_sites = resolve_enabled_sites(
        runtime.app_paths.config_file,
        enable_sites=args.enable_site,
        disable_sites=args.disable_site,
    )
    config_path = write_default_settings(
        runtime.app_paths,
        enabled_sites=enabled_sites,
        share_profile_with_arknights=args.share_arknights_profile,
        force=args.force,
    )
    runtime.stdout.write(f"Initialized config at {config_path}\n")
    return 0
