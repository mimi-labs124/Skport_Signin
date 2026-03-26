param(
    [string]$TaskName = "EFCheck Endfield Sign-In",
    [int]$DelaySeconds = 90,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

if (-not (Test-IsAdministrator)) {
    $selfPath = $MyInvocation.MyCommand.Path
    $elevatedArguments = @(
        "-NoProfile"
        "-ExecutionPolicy"
        "Bypass"
        "-File"
        "`"$selfPath`""
        "-TaskName"
        "`"$TaskName`""
        "-DelaySeconds"
        $DelaySeconds
    )
    if ($NoPause) {
        $elevatedArguments += "-NoPause"
    }

    try {
        Start-Process -FilePath "powershell.exe" -ArgumentList $elevatedArguments -Verb RunAs | Out-Null
        Write-Host "Elevation requested. Approve the UAC prompt to register the scheduled task."
        exit 0
    }
    catch {
        throw "Administrator permission is required to register the scheduled task."
    }
}

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
if (-not $NoPause) {
    PAUSE
}
