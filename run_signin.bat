@echo off
setlocal
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  ".venv\Scripts\python.exe" sign_in.py %*
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python sign_in.py %*
  ) else (
    py -3 sign_in.py %*
  )
)
pause
endlocal
