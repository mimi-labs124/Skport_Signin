@echo off
setlocal
cd /d "%~dp0"

call ".\setup_windows.bat" --no-pause
if errorlevel 1 (
  echo Setup failed.
  exit /b 1
)

set "PYTHON_RUNNER="
if exist ".venv\Scripts\python.exe" (
  set "PYTHON_RUNNER=.venv\Scripts\python.exe"
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    set "PYTHON_RUNNER=python"
  ) else (
    set "PYTHON_RUNNER=py -3"
  )
)

echo.
set /p INCLUDE_ARKNIGHTS=Include Arknights sign-in too? [Y/N]:
set "CONFIGURE_ARGS="
if /I "%INCLUDE_ARKNIGHTS%"=="Y" (
  echo.
  set /p SHARE_PROFILE=Share Endfield browser profile with Arknights? [Y/N]:
  set "CONFIGURE_ARGS=--include-arknights"
  if /I "%SHARE_PROFILE%"=="Y" (
    set "CONFIGURE_ARGS=%CONFIGURE_ARGS% --share-arknights-profile"
  )
)

%PYTHON_RUNNER% configure_sites.py %CONFIGURE_ARGS%
if errorlevel 1 exit /b 1

echo.
set /p CAPTURE_NOW=Capture your sign-in session now? [Y/N]:
if /I "%CAPTURE_NOW%"=="Y" (
  %PYTHON_RUNNER% capture_session.py --site endfield
  if errorlevel 1 exit /b 1

  if /I "%INCLUDE_ARKNIGHTS%"=="Y" (
    echo.
    echo Continue with the Arknights page in the same guided capture flow.
    %PYTHON_RUNNER% capture_session.py --site arknights
    if errorlevel 1 exit /b 1
  )
)

echo.
set /p REGISTER_TASK=Register the Windows logon scheduled task now? [Y/N]:
if /I "%REGISTER_TASK%"=="Y" (
  call ".\register_logon_task.bat" --no-pause
  if errorlevel 1 exit /b 1
)

echo.
echo EFCheck setup flow finished.
echo Manual tools remain available: capture_session.bat, run_signin.bat, register_logon_task.bat
pause
endlocal
