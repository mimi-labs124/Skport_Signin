from __future__ import annotations

import subprocess

from efcheck.statuses import NOTIFY_STATUSES


def should_notify_status(status: str) -> bool:
    return status in NOTIFY_STATUSES


def notify_status(status: str, title: str, message: str) -> None:
    if not should_notify_status(status):
        return
    show_windows_notification(title, message)


def show_windows_notification(title: str, message: str) -> None:
    escaped_title = title.replace("'", "''")
    escaped_message = message.replace("'", "''")
    command = (
        "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Windows.Forms');"
        "[void][System.Reflection.Assembly]::LoadWithPartialName('System.Drawing');"
        "$notify = New-Object System.Windows.Forms.NotifyIcon;"
        "$notify.Icon = [System.Drawing.SystemIcons]::Warning;"
        "$notify.BalloonTipTitle = '{title}';"
        "$notify.BalloonTipText = '{message}';"
        "$notify.Visible = $true;"
        "$notify.ShowBalloonTip(10000);"
        "Start-Sleep -Seconds 6;"
        "$notify.Dispose();"
    ).format(title=escaped_title, message=escaped_message)
    subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-Command",
            command,
        ],
        check=False,
        capture_output=True,
        text=True,
    )
