# EFCheck

[繁體中文說明](./README.zh-TW.md)

EFCheck is a Windows-first helper for the Arknights: Endfield daily sign-in page on SKPORT.

It uses a dedicated Playwright browser profile, keeps your saved login session in a local folder, runs headlessly, and can be triggered automatically at Windows logon.

## Highlights

- Headless browser sign-in with a dedicated local profile
- Up to 2 attempts per day by default
- Stops retrying after `SUCCESS` or `ALREADY_DONE`
- Windows desktop notification when the saved session appears to be expired
- Batch scripts for setup, session capture, and manual runs

## Requirements

- Windows
- Python 3.11 or newer
- Google Chrome or the Playwright-managed Chromium runtime

## Quick start

1. Run the guided setup:

```bat
install_efcheck.bat
```

This guided flow installs dependencies, offers to capture your session, and can register the Windows logon task for you.

If you prefer the manual path, run `setup_windows.bat` first. If you update from an older install, run it again so `tzdata` is installed too.

2. Capture your session once:

```bat
capture_session.bat
```

3. In the opened browser window, sign in and wait until the Endfield sign-in dashboard is visible.

4. Return to the terminal and press Enter to save the session.

5. Test one manual run:

```bat
run_signin.bat
```

## Scheduling

Register a Windows Task Scheduler entry in an elevated PowerShell window:

```powershell
register_logon_task.bat
```

If the script is not already running as administrator, it now relaunches itself and asks for UAC approval automatically.

The helper adds a short delay after logon before launching the sign-in command.
The scheduled task now runs through a hidden PowerShell action, so it should not leave a `cmd` window sitting on screen after logon.

## Configuration

Create a local config file only if you want to override the defaults:

```powershell
copy config\settings.example.json config\settings.json
```

Main settings:

- `timezone`: date boundary used for daily retry limits
- `browser_profile_dir`: local folder for the dedicated browser profile
- `browser_channel`: leave empty to use the Playwright-managed Chromium build
- `headless`: whether the sign-in browser runs without a visible window
- `timeout_seconds`: timeout for page and network waits
- `max_attempts_per_day`: default `2`

## Runtime behavior

- First successful run of the day stops further retries
- `ALREADY_DONE` also stops further retries
- Failed or expired-session runs can use the second daily attempt
- If the session looks expired, EFCheck shows a Windows desktop notification

## Included scripts

- [`sign_in.py`](./sign_in.py): main sign-in runner
- [`capture_session.py`](./capture_session.py): one-time login and session capture
- [`install_efcheck.bat`](./install_efcheck.bat): guided setup for installation, session capture, and task registration
- [`setup_windows.bat`](./setup_windows.bat): one-click Windows setup
- [`capture_session.bat`](./capture_session.bat): one-click session capture
- [`run_signin.bat`](./run_signin.bat): manual/background run entry used by Task Scheduler
- [`register_logon_task.bat`](./register_logon_task.bat): one-click scheduled-task wrapper
- [`register_logon_task.ps1`](./register_logon_task.ps1): Task Scheduler helper
- [`tools/package_windows_release.ps1`](./tools/package_windows_release.ps1): build a Windows zip release
- [`config/settings.example.json`](./config/settings.example.json): sample config

## Packaging a Windows release

Create a zip package with:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

The output zip is created in `dist/`.

## Notes

- Keep your local `state/`, `logs/`, and real `config/settings.json` private
- If the saved session expires, run `capture_session.bat` again
- Website structure or policies may change over time
- The `tests/` folder is intentionally tracked to document expected behavior and catch regressions
- See [`SECURITY.md`](./SECURITY.md) before sharing or publishing anything built from your local workspace
- This project is unofficial and is not affiliated with Hypergryph or SKPORT
