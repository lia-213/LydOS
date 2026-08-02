# 11-checkout.ps1
# Tests: ugit checkout <commit-oid-or-branch-or-tag>
#
# Tags added: commit 1 gets tagged as 'v1'. This script now checks out via
# the OID, then via the tag name, then via the branch name -- exercising all
# three ways get_oid() can resolve a target.

$ErrorActionPreference = "Stop"
$dir = "test-checkout"

Write-Host "`n=== ugit checkout ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1: just a.txt"
ugit tag v1 $c1

"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit 2: adds b.txt"

Write-Host "`n--- Checking out commit 1 by OID (should detach HEAD, remove b.txt) ---"
ugit checkout $c1

if ((Test-Path a.txt) -and -not (Test-Path b.txt)) {
    Write-Host "  [PASS] Working dir matches commit 1 (a.txt present, b.txt gone)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Working dir does not match commit 1" -ForegroundColor Red
}

$headRaw = Get-Content .ugit\HEAD -Raw
if ($headRaw.Trim() -eq $c1) {
    Write-Host "  [PASS] HEAD is detached, pointing directly at $c1" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] HEAD content unexpected: $headRaw" -ForegroundColor Red
}

Write-Host "`n--- Checking out commit 1 again, this time via its tag 'v1' ---"
ugit checkout v1

if ((Test-Path a.txt) -and -not (Test-Path b.txt)) {
    Write-Host "  [PASS] Checking out tag v1 resolves to the same snapshot as the raw OID" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Tag checkout produced an unexpected working dir" -ForegroundColor Red
}

Write-Host "`n--- Checking out 'master' by branch name (should reattach HEAD, restore b.txt) ---"
ugit checkout master

if ((Test-Path a.txt) -and (Test-Path b.txt)) {
    Write-Host "  [PASS] Working dir matches master (both files present)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Working dir does not match master" -ForegroundColor Red
}

$headRaw2 = Get-Content .ugit\HEAD -Raw
if ($headRaw2 -match "ref: refs.heads.master") {
    Write-Host "  [PASS] HEAD is symbolic again, pointing at refs/heads/master" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] HEAD not symbolic after checking out branch: $headRaw2" -ForegroundColor Red
}

Write-Host "`n=== Commit graph after test (tag: v1) ===" -ForegroundColor Cyan
ugit k

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
