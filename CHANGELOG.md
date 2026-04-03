# Changelog

All notable changes to Skport_Signin will be documented in this file.

The format is based on Keep a Changelog and uses a simple `major.minor.patch` versioning scheme.


## [Unreleased]

## [0.3.1] - 2026-04-03

### Fixed

- Removed UTF-8 BOM from `pyproject.toml` and Windows batch wrappers so CI and `cmd.exe` no longer fail on parse
- Fixed guided installer argument assembly so enabled sites are not passed as both enabled and disabled
- Hardened Windows installer wrappers to detect broken `.venv` interpreters and rebuild them automatically
- Added Python launcher fallback discovery for Windows installs where `py` or `python` is not available on `PATH`

## [0.3.0] - 2026-04-03

### Added

- Catalog-driven known-site configuration that writes both `endfield` and `arknights` into config with per-site `enabled` flags
- Generic `configure-sites` CLI flags for enabling/disabling known sites instead of a hardcoded Arknights toggle
- Release checksum output (`Skport_Signin-SHA256.txt`) alongside Windows release archives

### Changed

- Simplified the daily gate to same-day completion tracking only; retry counting was removed from new state files and active config
- Updated guided setup to ask which sites to enable and whether Arknights should share the Endfield profile only when both are enabled
- Refreshed `settings.example.json`, README docs, and release guidance for the enabled/disabled site model
- Bumped package and release metadata from `0.2.0` to `0.3.0`

## [0.2.0] - 2026-04-03

### Added

- Python package metadata with `skport_signin` console entry point
- Unified CLI with `run`, `capture-session`, `configure-sites`, `register-task`, `doctor`, `paths`, `package onedir`, and `package onefile`
- Centralized source-mode vs packaged-mode path resolution
- Config initialization and doctor commands
- PyInstaller build helpers and Windows packaging scripts
- Release and packaging documentation
- Additional tests for paths, CLI, doctor, packaging, and release docs

### Changed

- Moved core runtime behavior behind package command modules
- Converted root Python entry scripts into thin legacy shims
- Updated batch wrappers to prefer `skport_signin.exe` and otherwise call `python -m skport_signin`
- Updated task registration to schedule the unified CLI run path
- Improved repo documentation for source mode, packaged mode, and sensitive data handling
