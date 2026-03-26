@echo off
setlocal
cd /d "%~dp0"

where py >nul 2>nul
if %errorlevel%==0 (
  set "PYTHON_CMD=py -3"
) else (
  set "PYTHON_CMD=python"
)

if not exist ".venv\Scripts\python.exe" (
  %PYTHON_CMD% -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
playwright install chromium

if not exist "config\settings.json" (
  copy /Y "config\settings.example.json" "config\settings.json" >nul
)

echo Setup complete.
echo Next: run capture_session.bat
endlocal
