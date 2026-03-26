@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" capture_session.py %*
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python capture_session.py %*
  ) else (
    py -3 capture_session.py %*
  )
)
pause
endlocal
