# 00-run-all.ps1
# Runs every numbered test script in this folder, in order.
# Each individual script creates/cleans its own test-* subfolder, so they
# don't interfere with each other. Run this from inside the folder that
# contains all the 0X-*.ps1 scripts.

$ErrorActionPreference = "Continue"

$scripts = Get-ChildItem -Path $PSScriptRoot -Filter "*.ps1" |
    Where-Object { $_.Name -ne "00-run-all.ps1" } |
    Sort-Object Name

foreach ($script in $scripts) {
    Write-Host "`n`n########################################" -ForegroundColor Magenta
    Write-Host "# Running $($script.Name)" -ForegroundColor Magenta
    Write-Host "########################################" -ForegroundColor Magenta
    & $script.FullName
}

Write-Host "`n`nAll scripts finished. Scroll up for [PASS]/[FAIL]/[INFO] lines." -ForegroundColor Cyan
