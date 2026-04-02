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
It also asks whether to add the Arknights sign-in page and whether Arknights should share the Endfield browser profile.

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

The scheduled task uses Task Scheduler's own logon delay and then runs a hidden PowerShell command that starts `sign_in.py`.
`run_signin.bat` remains available for manual runs, but it is not the task action itself.

## Configuration

Create a local config file only if you want to override the defaults:

```powershell
copy config\settings.example.json config\settings.json
```

Main settings:

- `timezone`: date boundary used for daily retry limits
- `browser_channel`: leave empty to use the Playwright-managed Chromium build
- `headless`: whether the sign-in browser runs without a visible window
- `timeout_seconds`: timeout for page and network waits
- `max_attempts_per_day`: default `2`
- `sites`: list of sign-in targets to process in one run

Each site entry supports:

- `key`: stable site identifier used by `capture_session.py --site`
- `name`: label used in logs and console output
- `enabled`: whether this site is included in scheduled/manual runs
- `signin_url`: SKPORT sign-in page for the game
- `attendance_path`: attendance API path used to validate the run
- `state_path`: per-site retry gate file
- `browser_profile_dir`: browser profile directory for shared or separate sessions

To add Arknights with the same login session, add a second entry that points to the same `browser_profile_dir`:

```json
{
  "key": "arknights",
  "name": "Arknights",
  "enabled": true,
  "signin_url": "https://game.skport.com/arknights/sign-in",
  "attendance_path": "/api/v1/game/attendance",
  "state_path": "../state/arknights-last_run.json",
  "browser_profile_dir": "../state/browser-profile"
}
```

If you want Arknights to keep a separate session, change only `browser_profile_dir` to a different folder.

## Runtime behavior

- First successful run of the day stops further retries
- `ALREADY_DONE` also stops further retries
- Failed or expired-session runs can use the second daily attempt
- If the session looks expired, EFCheck shows a Windows desktop notification
- Enabled sites run sequentially in one invocation, each with its own retry gate file

## Included scripts

- [`sign_in.py`](./sign_in.py): main sign-in runner
- [`capture_session.py`](./capture_session.py): one-time login and session capture (`--site arknights` to target another configured site)
- [`install_efcheck.bat`](./install_efcheck.bat): guided setup for installation, session capture, and task registration
- [`setup_windows.bat`](./setup_windows.bat): one-click Windows setup
- [`capture_session.bat`](./capture_session.bat): one-click session capture
- [`run_signin.bat`](./run_signin.bat): manual run helper
- [`register_logon_task.bat`](./register_logon_task.bat): one-click scheduled-task wrapper
- [`register_logon_task.ps1`](./register_logon_task.ps1): creates the hidden PowerShell logon task for `sign_in.py`
- [`tools/package_windows_release.ps1`](./tools/package_windows_release.ps1): build a Windows zip release
- [`config/settings.example.json`](./config/settings.example.json): sample config

## Packaging a Windows release

Create a zip package with:

```powershell
powershell -ExecutionPolicy Bypass -File .\tools\package_windows_release.ps1
```

The output zip is created in `dist/`.

## Multi-site notes

- Legacy single-site configs still work; they are treated as an Endfield-only setup.
- `capture_session.py` defaults to `--site endfield`.
- Guided setup can add Arknights automatically and choose whether it shares the Endfield browser profile.
- A live check of the logged-in Arknights page currently shows:
  - GET `https://zonai.skport.com/api/v1/game/attendance?gameId=1&uid=...`
  - POST `https://zonai.skport.com/api/v1/game/attendance`
- The default Arknights `attendance_path` is therefore `/api/v1/game/attendance`.
- If SKPORT changes the endpoint or DOM flow, update `attendance_path` and re-test that site live.

## Notes

- Keep your local `state/`, `logs/`, and real `config/settings.json` private
- If the saved session expires, run `capture_session.bat` again
- Website structure or policies may change over time
- The `tests/` folder is intentionally tracked to document expected behavior and catch regressions
- See [`SECURITY.md`](./SECURITY.md) before sharing or publishing anything built from your local workspace
- This project is unofficial and is not affiliated with Hypergryph or SKPORT
