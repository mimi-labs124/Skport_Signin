# Security Notes

Skport_Signin stores an authenticated browser session in a local Playwright persistent profile.

Treat the following as sensitive data:

- `state/browser-profile/`
- `state/*-browser-profile/`
- `%LOCALAPPDATA%\Skport_Signin\browser-profile\`
- `state/`
- `logs/`
- `config/settings.json`
- any exported cookies, local storage, request dumps, or response dumps

Do not upload or share those files.

## Before publishing or sharing

Check that you are **not** including:

- `state/`
- `logs/`
- real `config/settings.json`
- browser profile directories
- copied request/response payloads
- generated `.zip` release artifacts that were built from a dirty workspace

## If you think a session was exposed

1. Invalidate or log out the affected SKPORT session.
2. Delete the affected local browser profile directory or directories.
3. Run `capture_session.bat` again to create a fresh session.
4. Rotate any other credentials that may have been stored in the same browser profile.

## Reporting

This is an unofficial personal-use automation helper. If you find a security issue in the repo itself, open a private report through the repository owner instead of posting secrets in a public issue.
