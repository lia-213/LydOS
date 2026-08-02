# 13-branch.ps1
# Tests: ugit branch [<name>] [<start-point>]
#
# Tags added: the commit that 'feature' branches off of gets tagged as
# 'branch-point', so the graph shows exactly where the two branches diverge,
# separate from wherever master/feature currently point after further commits.

$ErrorActionPreference = "Stop"
$dir = "test-branch"

Write-Host "`n=== ugit branch ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1"
ugit tag branch-point $c1

Write-Host "`n--- Creating branch 'feature' at current HEAD ---"
ugit branch feature

if (Test-Path ".ugit\refs\heads\feature") {
    $branchOid = (Get-Content ".ugit\refs\heads\feature" -Raw).Trim()
    if ($branchOid -eq $c1) {
        Write-Host "  [PASS] Branch 'feature' correctly points at $c1" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Branch 'feature' points at wrong oid: $branchOid" -ForegroundColor Red
    }
} else {
    Write-Host "  [FAIL] refs/heads/feature was not created" -ForegroundColor Red
}

Write-Host "`n--- Checking out the new branch and committing on it ---"
ugit checkout feature
"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit 2 on feature"
ugit tag feature-tip $c2

$masterOid = (Get-Content ".ugit\refs\heads\master" -Raw).Trim()
if ($masterOid -eq $c1) {
    Write-Host "  [PASS] master untouched by commits made on feature branch" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] master unexpectedly moved" -ForegroundColor Red
}

Write-Host "`n--- Listing branches (bare 'ugit branch', no args) ---"
try {
    ugit branch
    Write-Host "  [PASS] Branch listing ran without error" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] Branch listing raised an error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n=== Commit graph (tags: branch-point, feature-tip) ===" -ForegroundColor Cyan
ugit k

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
