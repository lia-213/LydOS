# 19-fetch.ps1
# Tests: ugit fetch <remote-path>
#
# Tags added: the remote's commit gets tagged 'remote-tip' before fetching,
# so both graphs below show a clear landmark. After fetching, the LOCAL
# repo's graph should show a refs/remote/master ref pointing at the same
# commit the REMOTE repo's own refs/heads/master points at.

$ErrorActionPreference = "Stop"
$remoteDir = "test-fetch-remote"
$localDir = "test-fetch-local"

Write-Host "`n=== ugit fetch ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $remoteDir, $localDir -ErrorAction SilentlyContinue

# --- Set up the "remote" repo ---
New-Item -ItemType Directory -Path $remoteDir | Out-Null
Push-Location $remoteDir
ugit init
"remote content" | Out-File -Encoding ascii remote.txt
ugit add remote.txt
$remoteCommit = ugit commit -m "commit made on remote"
ugit tag remote-tip $remoteCommit
Write-Host "  remote commit = $remoteCommit"

Write-Host "`n--- Remote repo's own graph (before fetch) ---" -ForegroundColor Cyan
ugit k
Pop-Location

# --- Set up the local repo, then fetch from the remote ---
New-Item -ItemType Directory -Path $localDir | Out-Null
Push-Location $localDir
ugit init

$remotePath = (Resolve-Path "../$remoteDir").Path
Write-Host "`n--- Fetching from $remotePath ---"
try {
    ugit fetch $remotePath
    Write-Host "  [PASS] fetch command ran without error" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] fetch raised an error: $($_.Exception.Message)" -ForegroundColor Red
}

if (Test-Path ".ugit/objects/$remoteCommit") {
    Write-Host "  [PASS] Remote commit object copied into local object store" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Remote commit object NOT found locally (see note re: ref path separators)" -ForegroundColor Red
}

Write-Host "`n--- Local repo's graph AFTER fetch (should show refs/remote/master) ---" -ForegroundColor Cyan
ugit k

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Compare the two 'ugit k' outputs above: the remote's refs/heads/master" -ForegroundColor Yellow
Write-Host "and the local's refs/remote/master should point at the same commit oid." -ForegroundColor Yellow
