param()

$ErrorActionPreference = "Stop"

$scriptRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$pathsToRemove = @(
    "logs",
    "state",
    "__pycache__",
    "efcheck\__pycache__",
    "tests\__pycache__",
    "config\settings.json"
)

foreach ($relativePath in $pathsToRemove) {
    $targetPath = Join-Path $scriptRoot $relativePath
    if (Test-Path $targetPath) {
        Remove-Item $targetPath -Recurse -Force
        Write-Host "Removed $relativePath"
    }
}

Write-Host "Public repo cleanup complete."
