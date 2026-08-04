# 12-tag.ps1
# Tests: ugit tag <name> [<oid>]

$ErrorActionPreference = "Stop"
$dir = "test-tag"

Write-Host "`n=== ugit tag ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1"

Write-Host "`n--- Tagging current HEAD as 'v1.0' (no explicit oid) ---"
ugit tag v1.0

if (Test-Path ".ugit/refs/tags/v1.0") {
    $tagValue = (Get-Content ".ugit/refs/tags/v1.0" -Raw).Trim()
    if ($tagValue -eq $c1) {
        Write-Host "  [PASS] Tag v1.0 correctly points at $c1" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Tag v1.0 points at wrong oid: $tagValue" -ForegroundColor Red
    }
} else {
    Write-Host "  [FAIL] refs/tags/v1.0 file was not created" -ForegroundColor Red
}

"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit 2"

Write-Host "`n--- Tagging an explicit older commit as 'v0.9' ---"
ugit tag v0.9 $c1

$tagValue2 = (Get-Content ".ugit/refs/tags/v0.9" -Raw).Trim()
if ($tagValue2 -eq $c1) {
    Write-Host "  [PASS] Tag v0.9 correctly points at explicit oid $c1" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Tag v0.9 points at wrong oid: $tagValue2" -ForegroundColor Red
}

Write-Host "`n--- Checking out via tag name ---"
ugit checkout v0.9
if ((Test-Path a.txt) -and -not (Test-Path b.txt)) {
    Write-Host "  [PASS] Checking out tag v0.9 restores commit 1's snapshot" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Checkout via tag did not produce expected snapshot" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
