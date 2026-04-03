# EFCheck

[繁體中文版](./README.zh-TW.md)

EFCheck is an unofficial Windows-first automation helper for the SKPORT daily sign-in pages used by Arknights: Endfield and Arknights.

It supports two operating modes:

- Source mode: clone the repository and run it with Python
- Packaged mode: use the Windows `onedir` or `onefile` build outputs

EFCheck stores browser session state locally and never expects those files to be published. Read [SECURITY.md](./SECURITY.md) before sharing anything built from your workspace.

## What it does

- Captures a Playwright browser profile and reuses the saved session
- Signs in one or more enabled SKPORT game pages in sequence
- Writes a full known-site config with per-site `enabled: true/false`
- Keeps per-site same-day completion state so completed sites are skipped on later runs
- Can register a Windows logon scheduled task
- Supports a unified CLI and compatibility batch wrappers
- Can be packaged as:
  - a portable one-folder Windows build
  - a single-file Windows executable with external browser bootstrap

## Supported platform

- Windows is the supported target
- Python 3.11+ is required for source mode
- Playwright Chromium is required for actual sign-in and session capture

## Sensitive files

Never publish or share these:

- `state/`
- `logs/`
- real `config/settings.json`
- any browser profile directory
- any copied cookie/session dump

Those locations may contain cookies, local storage, access tokens, or other login material.

## Quick start

### Source mode

1. Clone the repo.
2. Run the guided installer:

```bat
install_efcheck.bat
```

The guided flow will:

- install the Python package into `.venv`
- initialize local config
- ask which known sites to enable
- optionally let Arknights share the Endfield browser profile when both are enabled
- optionally capture sessions for the enabled sites
- optionally register the Windows logon task

### Packaged mode

Use either the `onedir` or `onefile` release output and run:

```bat
install_efcheck.bat
```

In packaged mode the wrappers prefer `efcheck.exe` automatically.

## Unified CLI

The package entry point is:

```powershell
python -m efcheck --help
```

or, after installation:

```powershell
efcheck --help
```

Available commands:

- `efcheck init`
- `efcheck run`
- `efcheck capture-session`
- `efcheck configure-sites`
- `efcheck register-task`
- `efcheck doctor`
- `efcheck paths`
- `efcheck package onedir`
- `efcheck package onefile`

`efcheck package ...` is source-mode only. A packaged `efcheck.exe` can run the operational commands, but it is not intended to rebuild PyInstaller artifacts.

## Site configuration model

`settings.json` always contains the full known-site list. Currently that means:

- `endfield`
- `arknights`

Each site stays in config even when disabled. Toggle sites with:

```powershell
python -m efcheck configure-sites --enable-site endfield --disable-site arknights
python -m efcheck configure-sites --enable-site arknights --share-arknights-profile
```

The active gate is completion-only:

- if a site already reached `SUCCESS` or `ALREADY_DONE` today, that site is skipped
- if a site failed earlier today, EFCheck allows another run

There is no active retry counter in the current config or newly written state files.

## Typical workflow

### 1. Initialize config

```powershell
python -m efcheck init
```

This creates a default `settings.json` if one does not already exist. The default config enables Endfield and keeps Arknights present but disabled.

### 2. Inspect resolved paths

```powershell
python -m efcheck paths --json
```

Config resolution order:

1. `--config`
2. `EFCHECK_CONFIG`
3. packaged-mode default: `%LOCALAPPDATA%\EFCheck\config\settings.json`
4. source-mode default: `<repo>\config\settings.json`

Base directory resolution order:

1. `--base-dir`
2. `EFCHECK_BASE_DIR`
3. packaged-mode default: `%LOCALAPPDATA%\EFCheck`
4. source-mode default: repository root

### 3. Capture sessions

```powershell
python -m efcheck capture-session --site endfield
```

If Arknights is enabled too:

```powershell
python -m efcheck capture-session --site arknights
```

### 4. Test a run

```powershell
python -m efcheck run --dry-run --force
python -m efcheck run --force
```

### 5. Register the Windows logon task

```powershell
python -m efcheck register-task
```

The compatibility wrapper is still available:

```bat
register_logon_task.bat
```

## Source mode vs packaged mode

### Source mode defaults

- Config: `<repo>/config/settings.json`
- State: `<repo>/state/`
- Logs: `<repo>/logs/`
- Existing source-mode configs remain compatible

### Packaged mode defaults

- Base dir: `%LOCALAPPDATA%\EFCheck`
- Config: `%LOCALAPPDATA%\EFCheck\config\settings.json`
- State: `%LOCALAPPDATA%\EFCheck\state\`
- Logs: `%LOCALAPPDATA%\EFCheck\logs\`
- Runtime: `%LOCALAPPDATA%\EFCheck\runtime\`
- Browser profiles: `%LOCALAPPDATA%\EFCheck\browser-profile\`

## Browser runtime

### Source mode

You can still use the standard Playwright install flow:

```powershell
playwright install chromium
```

`setup_windows.bat` instead runs:

```powershell
python -m efcheck doctor --install-browser
```

That is the supported bootstrap path for this project.

### Packaged mode

The executable does not bundle a full Chromium browser runtime inside the executable itself.

Instead, run:

```powershell
efcheck doctor --install-browser
```

This installs the browser runtime into the packaged EFCheck data directory under `runtime/playwright-browsers`.

## one-folder vs one-file

### one-folder

- Preferred for reliability
- Faster startup
- Easier to debug
- Recommended for most users

### one-file

- More portable
- Slower startup because PyInstaller extracts at launch
- Still requires external browser bootstrap
- Best treated as a convenient CLI binary, not a fully self-contained browser payload

## Batch wrappers

These are kept for compatibility and user convenience:

- [`install_efcheck.bat`](./install_efcheck.bat)
- [`setup_windows.bat`](./setup_windows.bat)
- [`capture_session.bat`](./capture_session.bat)
- [`run_signin.bat`](./run_signin.bat)
- [`register_logon_task.bat`](./register_logon_task.bat)

They prefer `efcheck.exe` when present, otherwise they call `python -m efcheck ...`.

## Building packages

### Build onedir

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_onedir.ps1
```

Or from a source checkout:

```powershell
python -m efcheck package onedir
```

### Build onefile

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_onefile.ps1
```

Or from a source checkout:

```powershell
python -m efcheck package onefile
```

### Build release zips

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\package_release.ps1
```

This writes:

- `EFCheck-Windows-onedir.zip`
- `EFCheck-Windows-onefile.zip`
- `EFCheck-SHA256.txt`

Legacy wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

## Troubleshooting

- `Missing dependency: playwright ...`
  Install project dependencies and then bootstrap the browser runtime.
- `Missing file: Playwright Chromium is not installed ...`
  In source mode, run `playwright install chromium`. In packaged mode, run `efcheck doctor --install-browser`.
- `Browser profile not found ...`
  Run `capture-session` first.
- `SESSION_EXPIRED`
  Re-run session capture for the affected site.
- `Configuration error`
  Validate `settings.json`, especially booleans, integers, and site keys.
- No scheduled task visible
  Re-run `register-task` and approve the UAC elevation prompt.

## Known limitations

- This project depends on SKPORT page structure and request patterns. Site changes can break automation.
- Arknights and Endfield do not use the same attendance endpoint shape.
- onefile mode still depends on an external Playwright browser install.
- Session capture is inherently manual because it depends on an interactive login.

## Support this project

If EFCheck saves you time and you want to support ongoing maintenance, testing, and packaging work, you can support MimiLab on Ko-fi:

[Support EFCheck on Ko-fi](https://ko-fi.com/mimilab)

Support is completely optional. EFCheck remains an unofficial personal-use automation helper maintained in spare time.

## Development

See:

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [docs/packaging.md](./docs/packaging.md)
- [docs/release.md](./docs/release.md)
- [docs/repo-metadata.md](./docs/repo-metadata.md)
- [CHANGELOG.md](./CHANGELOG.md)
