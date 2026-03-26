param(
    [string]$OutputDir = "dist"
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$releaseRoot = Join-Path $scriptRoot $OutputDir
$packageDir = Join-Path $releaseRoot "EFCheck-Windows"
$zipPath = Join-Path $releaseRoot "EFCheck-Windows.zip"

if (Test-Path $packageDir) {
    Remove-Item $packageDir -Recurse -Force
}
if (Test-Path $zipPath) {
    Remove-Item $zipPath -Force
}

New-Item -ItemType Directory -Path $packageDir | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageDir "config") | Out-Null
New-Item -ItemType Directory -Path (Join-Path $packageDir "efcheck") | Out-Null

$files = @(
    "LICENSE",
    "README.md",
    "README.zh-TW.md",
    "requirements.txt",
    "sign_in.py",
    "capture_session.py",
    "run_signin.bat",
    "capture_session.bat",
    "setup_windows.bat",
    "register_logon_task.ps1",
    "config\settings.example.json"
)

foreach ($file in $files) {
    Copy-Item (Join-Path $scriptRoot $file) (Join-Path $packageDir $file) -Force
}

Copy-Item (Join-Path $scriptRoot "efcheck\*.py") (Join-Path $packageDir "efcheck") -Force

Compress-Archive -Path (Join-Path $packageDir "*") -DestinationPath $zipPath
Write-Host "Created package: $zipPath"
