@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" sign_in.py %*
) else (
  where py >nul 2>nul
  if %errorlevel%==0 (
    py -3 sign_in.py %*
  ) else (
    python sign_in.py %*
  )
)

endlocal
