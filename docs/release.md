# Release Guide

## Scope

This document covers GitHub release preparation and download guidance for Skport_Signin.

## What should users download?

For most users, recommend **onedir** first.

### onedir vs onefile

| Item | onedir | onefile |
|---|---|---|
| Best for most users | ✅ Yes | ⚠️ Only when single-file portability is required |
| Startup speed | ✅ Faster | ❌ Slower (self-extract on launch) |
| Debuggability | ✅ Easier (full unpacked files) | ⚠️ Harder |
| Browser bootstrap required | ✅ Yes (`skport_signin doctor --install-browser`) | ✅ Yes (`skport_signin doctor --install-browser`) |
| Typical release guidance | Default recommendation | Optional convenience build |

Important: **onefile is not a fully self-contained browser payload**. Users still need a browser bootstrap step.

## Recommended release assets

Use consistent asset names so users can choose quickly:

- `Skport_Signin-Windows-onedir.zip`
- `Skport_Signin-Windows-onefile.zip`
- `Skport_Signin-SHA256.txt`

`Skport_Signin-SHA256.txt` should include checksums for every uploaded asset.

## Suggested tag and release title

- Tag: `v0.3.1`
- Title: `v0.3.1 - Installer and packaging hotfixes`

## Versioning strategy

Use `major.minor.patch`.

- Patch: bug fixes, docs corrections, release-script fixes
- Minor: new commands, wrappers, packaging improvements, non-breaking config evolution
- Major: breaking config layout or CLI compatibility changes

## Recommended release notes structure

Use this order to keep notes readable for first-time users:

1. **What changed** (high-level highlights)
2. **Upgrade notes** (if any config or behavior adjustment is needed)
3. **Download guide** (which asset to pick: onedir vs onefile)
4. **Bootstrap reminder** (`skport_signin doctor --install-browser` for packaged mode)
5. **Known limitations** (site-structure dependency, manual session capture, unofficial status)

## Pre-release checklist

- Run `python -m unittest discover -s tests -v`
- Run `python -m ruff check .`
- Build `onedir`
- Build `onefile`
- Build release zips
- Generate SHA256 checksums for uploaded assets
- Confirm release archives contain:
  - executable output
  - wrappers
  - `README.md`
  - `README.zh-TW.md`
  - `LICENSE`
  - `SECURITY.md`
  - `config/settings.example.json`

## Notes for release descriptions

Always state:

- the project is unofficial
- source mode and packaged mode are both supported
- onefile still requires external Playwright browser bootstrap
- browser/session data remains local and should never be published
- the config now contains a full known-site list with per-site `enabled: true/false`
- same-day completion state is remembered, but retry counting is no longer part of the active gate
