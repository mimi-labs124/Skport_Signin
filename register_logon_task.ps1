param(
    [string]$TaskName = "EFCheck Endfield Sign-In",
    [int]$DelaySeconds = 90
)

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerPath = Join-Path $scriptRoot "run_signin.bat"

if (-not (Test-Path $runnerPath)) {
    throw "Runner not found: $runnerPath"
}

$command = "/c timeout /t $DelaySeconds /nobreak >nul & `"$runnerPath`""
$action = New-ScheduledTaskAction -Execute "cmd.exe" -Argument $command
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Run EFCheck at logon with a short delay and let the Python gate limit retries per day." `
    -Force

Write-Host "Registered task: $TaskName"
