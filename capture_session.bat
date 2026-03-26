@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" capture_session.py %*
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 capture_session.py %*
  ) else (
    python capture_session.py %*
  )
)

endlocal
