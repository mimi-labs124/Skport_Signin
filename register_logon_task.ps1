param(
    [string]$TaskName = "Skport_Signin Sign-In",
    [int]$DelaySeconds = 90,
    [switch]$NoPause
)

$ErrorActionPreference = "Stop"

function Test-IsAdministrator {
    $currentIdentity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentIdentity)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Get-ScheduledLaunchArguments {
    param(
        [string]$ScriptRoot
    )
    $escapedScriptRoot = $ScriptRoot.Replace("'", "''")
    $command = @"
Set-Location -LiteralPath '$escapedScriptRoot'
if (Test-Path '.\skport_signin.exe') {
    & '.\skport_signin.exe' run
    exit `$LASTEXITCODE
}
if (Test-Path '.\.venv\Scripts\python.exe') {
    & '.\.venv\Scripts\python.exe' -m skport_signin run
    exit `$LASTEXITCODE
}
if (Test-Path '.\.venv\Scripts\pythonw.exe') {
    & '.\.venv\Scripts\pythonw.exe' -m skport_signin run
    exit `$LASTEXITCODE
}
if (Get-Command py -ErrorAction SilentlyContinue) {
    & py -3 -m skport_signin run
    exit `$LASTEXITCODE
}
& python -m skport_signin run
exit `$LASTEXITCODE
"@

    $encodedCommand = [Convert]::ToBase64String([System.Text.Encoding]::Unicode.GetBytes($command))
    return "-NoProfile -WindowStyle Hidden -ExecutionPolicy Bypass -EncodedCommand $encodedCommand"
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
        Write-Host "Elevation requested. Approve the UAC prompt to register the scheduled task."
        $proc = Start-Process `
            -FilePath "powershell.exe" `
            -ArgumentList $elevatedArguments `
            -Verb RunAs `
            -PassThru `
            -Wait
        exit $proc.ExitCode
    }
    catch {
        throw "Administrator permission is required to register the scheduled task."
    }
}

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$scheduledArguments = Get-ScheduledLaunchArguments -ScriptRoot $scriptRoot
$action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument $scheduledArguments
$trigger = New-ScheduledTaskTrigger -AtLogOn -RandomDelay ([TimeSpan]::FromSeconds($DelaySeconds))
$settings = New-ScheduledTaskSettingsSet `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries `
    -MultipleInstances IgnoreNew

Register-ScheduledTask `
    -TaskName $TaskName `
    -Action $action `
    -Trigger $trigger `
    -Settings $settings `
    -Description "Run Skport_Signin at logon with a Task Scheduler delay and let the Python gate limit retries per day." `
    -Force

Write-Host "Registered task: $TaskName"
if (-not $NoPause) {
    PAUSE
}

