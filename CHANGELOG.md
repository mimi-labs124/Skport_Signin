# Changelog

All notable changes to EFCheck will be documented in this file.

The format is based on Keep a Changelog and uses a simple `major.minor.patch` versioning scheme.


## [Unreleased]

### Added

- Ko-fi support sections in `README.md` and `README.zh-TW.md` with optional-support wording
- Markdown issue templates for bug reports and feature requests
- Uppercase-path pull request template (`.github/PULL_REQUEST_TEMPLATE.md`) aligned with repository checklist expectations
- `docs/repo-metadata.md` for GitHub About and release naming recommendations
- Windows packaging smoke job in CI (`onedir` build + `efcheck.exe --help` smoke run)

### Changed

- Expanded `docs/release.md` with explicit download guidance (onedir vs onefile), checksum recommendation, and release-note structure
- Expanded `docs/packaging.md` with CI smoke-test scope and onefile exclusion rationale
- Updated `CONTRIBUTING.md` with issue/PR template and release workflow expectations

## [0.2.0] - 2026-04-03

### Added

- Python package metadata with `efcheck` console entry point
- Unified CLI with `run`, `capture-session`, `configure-sites`, `register-task`, `doctor`, `paths`, `package onedir`, and `package onefile`
- Centralized source-mode vs packaged-mode path resolution
- Config initialization and doctor commands
- PyInstaller build helpers and Windows packaging scripts
- Release and packaging documentation
- Additional tests for paths, CLI, doctor, packaging, and release docs

### Changed

- Moved core runtime behavior behind package command modules
- Converted root Python entry scripts into thin legacy shims
- Updated batch wrappers to prefer `efcheck.exe` and otherwise call `python -m efcheck`
- Updated task registration to schedule the unified CLI run path
- Improved repo documentation for source mode, packaged mode, and sensitive data handling
