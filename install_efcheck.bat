@echo off
setlocal
cd /d "%~dp0"

call ".\setup_windows.bat" --no-pause
if errorlevel 1 (
  echo Setup failed.
  exit /b 1
)

set "EFCHECK_CMD="
if exist ".\efcheck.exe" (
  set "EFCHECK_CMD=.\efcheck.exe"
) else if exist ".venv\Scripts\python.exe" (
  set "EFCHECK_CMD=.venv\Scripts\python.exe -m efcheck"
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    set "EFCHECK_CMD=python -m efcheck"
  ) else (
    set "EFCHECK_CMD=py -3 -m efcheck"
  )
)

echo.
set /p ENABLE_ENDFIELD=Enable Endfield sign-in? [Y/n]:
set /p ENABLE_ARKNIGHTS=Enable Arknights sign-in? [y/N]:

set "ENABLE_ENDFIELD_NORMALIZED=%ENABLE_ENDFIELD%"
if not defined ENABLE_ENDFIELD_NORMALIZED set "ENABLE_ENDFIELD_NORMALIZED=Y"
set "ENABLE_ARKNIGHTS_NORMALIZED=%ENABLE_ARKNIGHTS%"
if not defined ENABLE_ARKNIGHTS_NORMALIZED set "ENABLE_ARKNIGHTS_NORMALIZED=N"

if /I not "%ENABLE_ENDFIELD_NORMALIZED%"=="Y" if /I not "%ENABLE_ARKNIGHTS_NORMALIZED%"=="Y" (
  echo No site selected. Defaulting to Endfield enabled.
  set "ENABLE_ENDFIELD_NORMALIZED=Y"
)

set "CONFIGURE_ARGS=--disable-site endfield --disable-site arknights"
if /I "%ENABLE_ENDFIELD_NORMALIZED%"=="Y" (
  set "CONFIGURE_ARGS=%CONFIGURE_ARGS% --enable-site endfield"
)
if /I "%ENABLE_ARKNIGHTS_NORMALIZED%"=="Y" (
  set "CONFIGURE_ARGS=%CONFIGURE_ARGS% --enable-site arknights"
)

if /I "%ENABLE_ENDFIELD_NORMALIZED%"=="Y" if /I "%ENABLE_ARKNIGHTS_NORMALIZED%"=="Y" (
  echo.
  set /p SHARE_PROFILE=Share Endfield browser profile with Arknights? [Y/N]:
  if /I "%SHARE_PROFILE%"=="Y" (
    set "CONFIGURE_ARGS=%CONFIGURE_ARGS% --share-arknights-profile"
  )
)

%EFCHECK_CMD% configure-sites %CONFIGURE_ARGS%
if errorlevel 1 exit /b 1

echo.
set /p CAPTURE_NOW=Capture your sign-in session now? [Y/N]:
if /I "%CAPTURE_NOW%"=="Y" (
  if /I "%ENABLE_ENDFIELD_NORMALIZED%"=="Y" (
    %EFCHECK_CMD% capture-session --site endfield
    if errorlevel 1 exit /b 1
  )

  if /I "%ENABLE_ARKNIGHTS_NORMALIZED%"=="Y" (
    echo.
    echo Continue with the Arknights page in the same guided capture flow.
    %EFCHECK_CMD% capture-session --site arknights
    if errorlevel 1 exit /b 1
  )
)

echo.
set /p REGISTER_TASK=Register the Windows logon scheduled task now? [Y/N]:
if /I "%REGISTER_TASK%"=="Y" (
  %EFCHECK_CMD% register-task --no-pause
  if errorlevel 1 exit /b 1
)

echo.
echo EFCheck setup flow finished.
echo Manual tools remain available: capture_session.bat, run_signin.bat, register_logon_task.bat
pause
endlocal
