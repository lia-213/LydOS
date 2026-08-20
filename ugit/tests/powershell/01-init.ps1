# 01-init.ps1
# Tests: ugit init
# Run from your sandbox root (e.g. C:\Users\lydbo\ugit-sandbox)

$ErrorActionPreference = "Stop"
$dir = "test-init"

Write-Host "`n=== ugit init ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

# First init: should create .ugit fresh
ugit init

if (Test-Path ".ugit/objects") {
    Write-Host "  [PASS] .ugit/objects created" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] .ugit/objects missing" -ForegroundColor Red
}

if (Test-Path ".ugit/HEAD") {
    $head = Get-Content ".ugit/HEAD" -Raw
    if ($head -match "ref: refs.heads.master") {
        Write-Host "  [PASS] HEAD points symbolically at refs/heads/master" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] HEAD content unexpected: $head" -ForegroundColor Red
    }
} else {
    Write-Host "  [FAIL] .ugit/HEAD missing" -ForegroundColor Red
}

# Second init: should print the "reinitialised" bonus message, not error
Write-Host "`n--- Re-running init (should say 'Reinitialised') ---"
ugit init

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
