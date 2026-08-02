# 17-merge.ps1
# Tests: ugit merge <commit>
#
# Tags added: each branch tip gets tagged BEFORE merging, so the resulting
# graph shows exactly where each branch was pre-merge, distinct from where
# master ends up afterward (fast-forward moves master's pointer forward;
# the true 3-way case creates a brand new merge commit).

$ErrorActionPreference = "Stop"
$dir = "test-merge"

Write-Host "`n=== ugit merge (fast-forward case) ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1"
ugit tag base $c1

ugit branch feature
ugit checkout feature
"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit 2 on feature"
ugit tag feature-tip-before-ff $c2

ugit checkout master
Write-Host "`n--- Fast-forward merging 'feature' into master ---"
try {
    ugit merge $c2
    Write-Host "  [PASS] merge command ran" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] merge raised an error: $($_.Exception.Message)" -ForegroundColor Red
}

if (Test-Path b.txt) {
    Write-Host "  [PASS] b.txt now present on master after fast-forward merge" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] b.txt missing after merge" -ForegroundColor Red
}

Write-Host "`n=== Commit graph after fast-forward (tags: base, feature-tip-before-ff) ===" -ForegroundColor Cyan
ugit k

Pop-Location

Write-Host "`n=== ugit merge (true 3-way merge, diverged branches) ===" -ForegroundColor Cyan
$dir2 = "test-merge-3way"
Remove-Item -Recurse -Force $dir2 -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir2 | Out-Null
Push-Location $dir2

ugit init
"base content" | Out-File -Encoding ascii shared.txt
ugit add shared.txt
$base = ugit commit -m "base commit"
ugit tag merge-base $base

ugit branch feature
ugit checkout feature
"feature change" | Out-File -Encoding ascii feature-only.txt
ugit add feature-only.txt
$featureCommit = ugit commit -m "feature adds its own file"
ugit tag feature-tip $featureCommit

ugit checkout master
"master change" | Out-File -Encoding ascii master-only.txt
ugit add master-only.txt
$masterCommit = ugit commit -m "master adds its own file"
ugit tag master-tip-before-merge $masterCommit

Write-Host "`n--- Merging diverged 'feature' into master (needs diff3) ---"
try {
    ugit merge $featureCommit
    Write-Host "  [PASS] merge command ran (check working dir + 'ugit status' manually for conflicts)" -ForegroundColor Green
    if ((Test-Path feature-only.txt) -and (Test-Path master-only.txt)) {
        Write-Host "  [PASS] Both branches' unique files present after merge" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Expected files from both branches not both present" -ForegroundColor Red
    }
} catch {
    Write-Host "  [FAIL] 3-way merge raised an error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  (Check whether 'diff3' is installed and on PATH)" -ForegroundColor Yellow
}

Write-Host "`n=== Commit graph after 3-way merge attempt (tags: merge-base, feature-tip, master-tip-before-merge) ===" -ForegroundColor Cyan
ugit k

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
