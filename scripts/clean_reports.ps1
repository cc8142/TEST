$ErrorActionPreference = "Stop"
$paths = @("reports", ".pytest_cache")
foreach ($path in $paths) {
    if (Test-Path $path) {
        Remove-Item $path -Recurse -Force
    }
}
Write-Host "Cleaned reports and pytest cache."

