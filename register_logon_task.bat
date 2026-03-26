@echo off
setlocal
cd /d "%~dp0"

set "EXTRA_ARGS="
if /I "%~1"=="--no-pause" (
  set "EXTRA_ARGS=-NoPause"
)

powershell -NoProfile -ExecutionPolicy Bypass -File ".\register_logon_task.ps1" %EXTRA_ARGS%
set "EXIT_CODE=%ERRORLEVEL%"

if not "%~1"=="--no-pause" (
  pause
)

endlocal
exit /b %EXIT_CODE%
