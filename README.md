# Skport_Signin

[繁體中文版](./README.zh-TW.md)

Skport_Signin is an unofficial Windows-first automation helper for the SKPORT daily sign-in pages used by Arknights: Endfield and Arknights.

It supports two operating modes:

- Source mode: clone the repository and run it with Python
- Packaged mode: use the Windows `onedir` or `onefile` build outputs

Skport_Signin stores browser session state locally and never expects those files to be published. Read [SECURITY.md](./SECURITY.md) before sharing anything built from your workspace.

## What it does

- Captures a Playwright browser profile and reuses the saved session
- Signs in one or more enabled SKPORT game pages in sequence
- Writes a full known-site config with per-site `enabled: true/false`
- Keeps per-site same-day completion state so completed sites are skipped on later runs
- Can register a Windows logon scheduled task
- Includes one CLI entry point plus Windows batch launchers
- Can be packaged as:
  - a portable one-folder Windows build
  - a single-file Windows executable that still uses an external browser install

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
install_skport_signin.bat
```

The guided flow will:

- install the package into `.venv`
- install the Playwright Chromium runtime
- start `skport_signin setup --interactive`

### Packaged mode

Use either the `onedir` or `onefile` release output and run:

```bat
install_skport_signin.bat
```

In packaged mode the batch launchers use `skport_signin.exe` automatically when it is present.

## Unified CLI

The package entry point is:

```powershell
python -m skport_signin --help
```

or, after installation:

```powershell
skport_signin --help
```

Available commands:

- `skport_signin init`
- `skport_signin setup --interactive`
- `skport_signin run`
- `skport_signin capture-session`
- `skport_signin configure-sites`
- `skport_signin register-task`
- `skport_signin doctor`
- `skport_signin paths`
- `skport_signin package onedir`
- `skport_signin package onefile`

`skport_signin package ...` is source-mode only. A packaged `skport_signin.exe` can run the operational commands, but it is not intended to rebuild PyInstaller artifacts.

## Site configuration model

`settings.json` always contains the full known-site list. Currently that means:

- `endfield`
- `arknights`

Each site stays in config even when disabled. Toggle sites with:

```powershell
python -m skport_signin configure-sites --enable-site endfield --disable-site arknights
python -m skport_signin configure-sites --enable-site arknights --share-arknights-profile
```

The active gate is completion-only:

- if a site already reached `SUCCESS` or `ALREADY_DONE` today, that site is skipped
- if a site failed earlier today, Skport_Signin allows another run

There is no active retry counter in the current config or newly written state files.

## Typical workflow

### 1. Run guided setup

```powershell
python -m skport_signin setup --interactive
```

This guided flow creates config if needed, asks which sites to enable, can let Arknights share the Endfield profile, and can continue straight into session capture and task registration.

### 2. Initialize config manually

```powershell
python -m skport_signin init
```

This creates a default `settings.json` if one does not already exist. The default config enables Endfield and keeps Arknights present but disabled.

### 3. Inspect resolved paths

```powershell
python -m skport_signin paths --json
```

Config resolution order:

1. `--config`
2. `SKPORT_SIGNIN_CONFIG`
3. packaged-mode default: `%LOCALAPPDATA%\Skport_Signin\config\settings.json`
4. source-mode default: `<repo>\config\settings.json`

Base directory resolution order:

1. `--base-dir`
2. `SKPORT_SIGNIN_BASE_DIR`
3. packaged-mode default: `%LOCALAPPDATA%\Skport_Signin`
4. source-mode default: repository root

### 4. Capture sessions

```powershell
python -m skport_signin capture-session --site endfield
```

If Arknights is enabled too:

```powershell
python -m skport_signin capture-session --site arknights
```

### 5. Test a run

```powershell
python -m skport_signin run --dry-run --force
python -m skport_signin run --force
```

### 6. Register the Windows logon task

```powershell
python -m skport_signin register-task
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

- Base dir: `%LOCALAPPDATA%\Skport_Signin`
- Config: `%LOCALAPPDATA%\Skport_Signin\config\settings.json`
- State: `%LOCALAPPDATA%\Skport_Signin\state\`
- Logs: `%LOCALAPPDATA%\Skport_Signin\logs\`
- Runtime: `%LOCALAPPDATA%\Skport_Signin\runtime\`
- Browser profiles: `%LOCALAPPDATA%\Skport_Signin\browser-profile\`

## Browser runtime

### Source mode

You can still use the standard Playwright install flow:

```powershell
playwright install chromium
```

`setup_windows.bat` runs:

```powershell
python -m skport_signin doctor --install-browser
```

That is the recommended install path for this project.

### Packaged mode

The executable does not bundle a full Chromium browser runtime.

Instead, run:

```powershell
skport_signin doctor --install-browser
```

That installs the browser runtime into the packaged Skport_Signin data directory under `runtime/playwright-browsers`.

## one-folder vs one-file

### one-folder

- Preferred for reliability
- Faster startup
- Easier to debug
- Recommended for most users

### one-file

- More portable
- Slower startup because PyInstaller extracts at launch
- Still requires a separate browser install
- Best treated as a convenient CLI binary, not a fully self-contained browser package

## Batch wrappers

These are kept for compatibility and convenience:

- [`install_skport_signin.bat`](./install_skport_signin.bat)
- [`setup_windows.bat`](./setup_windows.bat)
- [`capture_session.bat`](./capture_session.bat)
- [`run_signin.bat`](./run_signin.bat)
- [`register_logon_task.bat`](./register_logon_task.bat)

They use `skport_signin.exe` when present, otherwise they call `python -m skport_signin ...`.

## Building packages

### Build onedir

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_onedir.ps1
```

Or from a source checkout:

```powershell
python -m skport_signin package onedir
```

### Build onefile

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\build_onefile.ps1
```

Or from a source checkout:

```powershell
python -m skport_signin package onefile
```

### Build release zips

```powershell
powershell -ExecutionPolicy Bypass -File .\packaging\package_release.ps1
```

This writes:

- `Skport_Signin-Windows-onedir.zip`
- `Skport_Signin-Windows-onefile.zip`
- `Skport_Signin-SHA256.txt`

Legacy wrapper:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

## Troubleshooting

- `setup --interactive` fails after config changes
  Run `skport_signin doctor --json` to inspect config validity, enabled sites, and writable path health.
- `Missing dependency: playwright ...`
  Install project dependencies and then install the browser runtime.
- `Missing file: Playwright Chromium is not installed ...`
  In source mode, run `playwright install chromium`. In packaged mode, run `skport_signin doctor --install-browser`.
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

If Skport_Signin saves you time and you want to support ongoing maintenance, testing, and packaging work, you can support MimiLab on Ko-fi:

[Support Skport_Signin on Ko-fi](https://ko-fi.com/mimilab)

Support is completely optional. Skport_Signin remains an unofficial personal-use automation helper maintained in spare time.

## Development

See:

- [CONTRIBUTING.md](./CONTRIBUTING.md)
- [docs/packaging.md](./docs/packaging.md)
- [docs/release.md](./docs/release.md)
- [docs/repo-metadata.md](./docs/repo-metadata.md)
- [CHANGELOG.md](./CHANGELOG.md)
