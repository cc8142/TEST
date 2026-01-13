param(
    [ValidateSet("all", "api", "ui", "smoke", "e2e")]
    [string]$Suite = "all",
    [string]$Env = "local",
    [string]$BaseUrl = "",
    [ValidateSet("chromium", "firefox", "webkit")]
    [string]$Browser = "chromium",
    [int]$Workers = 0,
    [int]$Reruns = 0,
    [switch]$Headed
)

$ErrorActionPreference = 'Stop'

$argsList = @(
    "tests\run_all.py",
    "--suite", $Suite,
    "--env", $Env,
    "--workers", $Workers,
    "--reruns", $Reruns,
    "--browser", $Browser,
    "--allure-report"
)

if ($BaseUrl) {
    $argsList += @("--base-url", $BaseUrl)
}

if ($Headed) {
    $argsList += "--headed"
}

python @argsList
Write-Host "Report generated at reports\summary.html"
