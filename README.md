# EFCheck

EFCheck is a small Windows-first helper for the Arknights: Endfield daily sign-in page.

It uses a dedicated Playwright browser profile, reuses your saved session, runs headlessly, and can be scheduled at logon.

## Features

- Headless browser sign-in with a dedicated local profile
- Up to 2 attempts per day by default
- Stops retrying after `SUCCESS` or `ALREADY_DONE`
- Windows desktop notification when the saved session appears to be expired
- Batch scripts for setup, session capture, and manual runs
- PowerShell helper to register a logon task
- Public-safe layout with local runtime data excluded by `.gitignore`

## Project files

- [`sign_in.py`](./sign_in.py): main sign-in runner
- [`capture_session.py`](./capture_session.py): one-time login/session capture
- [`setup_windows.bat`](./setup_windows.bat): one-click Windows setup
- [`capture_session.bat`](./capture_session.bat): one-click session capture
- [`run_signin.bat`](./run_signin.bat): one-click manual run
- [`register_logon_task.ps1`](./register_logon_task.ps1): Task Scheduler helper
- [`package_windows_release.ps1`](./package_windows_release.ps1): zip a public Windows release
- [`LICENSE`](./LICENSE): MIT license
- [`prepare_public_repo.bat`](./prepare_public_repo.bat): cleanup wrapper that bypasses PowerShell policy prompts
- [`prepare_public_repo.ps1`](./prepare_public_repo.ps1): remove local runtime data before publishing
- [`config/settings.example.json`](./config/settings.example.json): sample config

## Quick start

1. Run:

```bat
setup_windows.bat
```

2. Capture your login session:

```bat
capture_session.bat
```

3. In the opened browser window, sign in and wait until the dashboard is visible.

4. Go back to the terminal and press Enter to save the session.

5. Test the flow:

```bat
run_signin.bat
```

## Scheduling

Register a logon task in an elevated PowerShell window:

```powershell
powershell -ExecutionPolicy Bypass -File .\register_logon_task.ps1
```

The helper adds a short startup delay before running the sign-in command.

## Configuration

Copy the sample config if needed:

```powershell
copy config\settings.example.json config\settings.json
```

Main settings:

- `timezone`: date boundary used for daily retry limits
- `browser_profile_dir`: local folder for the dedicated browser profile
- `browser_channel`: leave empty to use the Playwright-managed Chromium build
- `headless`: whether the sign-in browser runs without a visible window
- `timeout_seconds`: timeout for page/network waits
- `max_attempts_per_day`: default `2`

## Runtime behavior

- First successful run of the day stops further retries
- `ALREADY_DONE` also stops further retries
- Failed or expired-session runs can use the second daily attempt
- If the session looks expired, EFCheck shows a Windows desktop notification

## Packaging a Windows release

Create a zip package with:

```powershell
powershell -ExecutionPolicy Bypass -File .\package_windows_release.ps1
```

The output zip is created in `dist/`.

## Preparing a public repository

Before your first public commit, remove local sessions, logs, caches, and personal config:

```bat
prepare_public_repo.bat
```

Or, if you prefer PowerShell directly:

```powershell
powershell -ExecutionPolicy Bypass -File .\prepare_public_repo.ps1
```

## Notes

- Do not publish your local `state/`, `logs/`, or real `config/settings.json`
- If the saved session expires, run `capture_session.bat` again
- Website structure or policies may change over time
- The `tests/` folder is intentionally tracked. It documents expected behavior and helps catch regressions in future site or workflow changes.
