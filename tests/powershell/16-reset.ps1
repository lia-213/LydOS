# 16-reset.ps1
# Tests: ugit reset <commit>
# NOTE: base.reset() only moves the HEAD ref -- it does NOT touch the index
# or working directory (unlike `git reset --hard`). This script checks that
# specific, more limited behaviour.
#
# Tags added: commit 2 gets tagged BEFORE the reset. Once we reset master
# back to commit 1, commit 2 becomes unreachable from master/HEAD -- the tag
# is what keeps it visible (and reachable) in the graph at all. That mirrors
# how a tag can rescue a commit from becoming "orphaned" the way your earlier
# detached-HEAD commit did.

$ErrorActionPreference = "Stop"
$dir = "test-reset"

Write-Host "`n=== ugit reset ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1"
ugit tag v1 $c1

"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit 2"
ugit tag pre-reset $c2

Write-Host "`n--- Before reset: master points at commit 2 ---"
$before = (Get-Content .ugit/refs/heads/master -Raw).Trim()
Write-Host "  master = $before (expected $c2)"

ugit reset $c1

Write-Host "`n--- After reset $c1 ---"
$after = (Get-Content .ugit/refs/heads/master -Raw).Trim()
Write-Host "  master = $after (expected $c1)"

if ($after -eq $c1) {
    Write-Host "  [PASS] master ref moved back to commit 1" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] master ref did not move as expected" -ForegroundColor Red
}

if (Test-Path b.txt) {
    Write-Host "  [INFO] b.txt still exists on disk after reset (expected: reset does not touch the working directory)" -ForegroundColor Yellow
} else {
    Write-Host "  [INFO] b.txt was removed from disk" -ForegroundColor Yellow
}

Write-Host "`n--- ugit log after reset (commit 2 unreachable from HEAD, but still tagged) ---"
$logOut = ugit log
Write-Host $logOut
if ($logOut -notmatch [regex]::Escape($c2)) {
    Write-Host "  [PASS] Commit 2 no longer reachable from HEAD via log" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Commit 2 still shows up in log" -ForegroundColor Red
}

Write-Host "`n--- Confirming commit 2 is still reachable via its tag ---"
$viaTag = ugit cat-file pre-reset
if ($viaTag -match "commit 2") {
    Write-Host "  [PASS] pre-reset tag still resolves to commit 2's content" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] pre-reset tag did not resolve as expected" -ForegroundColor Red
}

Write-Host "`n=== Commit graph after reset (tags: v1, pre-reset) ===" -ForegroundColor Cyan
ugit k

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
