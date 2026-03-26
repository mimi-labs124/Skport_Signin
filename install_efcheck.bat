@echo off
setlocal
cd /d "%~dp0"

call ".\setup_windows.bat" --no-pause
if errorlevel 1 (
  echo Setup failed.
  exit /b 1
)

echo.
set /p CAPTURE_NOW=Capture your sign-in session now? [Y/N]:
if /I "%CAPTURE_NOW%"=="Y" (
  if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" capture_session.py
  ) else (
    where py >nul 2>nul
    if errorlevel 1 (
      python capture_session.py
    ) else (
      py -3 capture_session.py
    )
  )
)

echo.
set /p REGISTER_TASK=Register the Windows logon scheduled task now? [Y/N]:
if /I "%REGISTER_TASK%"=="Y" (
  call ".\register_logon_task.bat" --no-pause
)

echo.
echo EFCheck setup flow finished.
echo Manual tools remain available: capture_session.bat, run_signin.bat, register_logon_task.bat
pause
endlocal
