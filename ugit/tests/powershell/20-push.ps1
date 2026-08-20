# 20-push.ps1
# Tests: ugit push <remote-path> <branch>
#
# Tags added: the local commit gets tagged 'local-tip' before pushing. The
# remote starts completely empty (no commits at all) -- this is the exact
# scenario that used to crash with a TypeError (see data.object_exists'
# None-guard fix). Graphs are shown for both repos before and after.

$ErrorActionPreference = "Stop"
$remoteDir = "test-push-remote"
$localDir = "test-push-local"

Write-Host "`n=== ugit push ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $remoteDir, $localDir -ErrorAction SilentlyContinue

# --- Set up an empty "remote" repo ---
New-Item -ItemType Directory -Path $remoteDir | Out-Null
Push-Location $remoteDir
ugit init
Write-Host "`n--- Remote repo's graph (empty, before push) ---" -ForegroundColor Cyan
ugit k
Pop-Location

# --- Set up local repo with a commit to push ---
New-Item -ItemType Directory -Path $localDir | Out-Null
Push-Location $localDir
ugit init
"local content" | Out-File -Encoding ascii local.txt
ugit add local.txt
$localCommit = ugit commit -m "commit made locally"
ugit tag local-tip $localCommit
Write-Host "  local commit = $localCommit"

Write-Host "`n--- Local repo's graph (before push) ---" -ForegroundColor Cyan
ugit k

$remotePath = (Resolve-Path "../$remoteDir").Path
Write-Host "`n--- Pushing local master to $remotePath ---"
try {
    ugit push $remotePath master
    Write-Host "  [PASS] push command ran without error" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] push raised an error: $($_.Exception.Message)" -ForegroundColor Red
}
Pop-Location

# --- Verify from the remote side ---
Write-Host "`n--- Checking remote repo after push ---"
if (Test-Path "$remoteDir/.ugit/objects/$localCommit") {
    Write-Host "  [PASS] Commit object copied to remote object store" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Commit object missing on remote" -ForegroundColor Red
}

if (Test-Path "$remoteDir/.ugit/refs/heads/master") {
    $remoteMasterValue = (Get-Content "$remoteDir/.ugit/refs/heads/master" -Raw).Trim()
    if ($remoteMasterValue -eq $localCommit) {
        Write-Host "  [PASS] Remote master ref updated to pushed commit" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] Remote master ref has wrong value: $remoteMasterValue" -ForegroundColor Red
    }
} else {
    Write-Host "  [FAIL] Remote refs/heads/master was not created" -ForegroundColor Red
}

Write-Host "`n--- Remote repo's graph AFTER push (should now show master pointing at the pushed commit) ---" -ForegroundColor Cyan
Push-Location $remoteDir
ugit k
Pop-Location

Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "Compare local's refs/heads/master (before) to remote's refs/heads/master" -ForegroundColor Yellow
Write-Host "(after) -- both should now point at the same pushed commit. Note: only" -ForegroundColor Yellow
Write-Host "the 'master' ref was pushed -- the 'local-tip' TAG stays local-only," -ForegroundColor Yellow
Write-Host "since push() only updates the one refname you pass it. The commit" -ForegroundColor Yellow
Write-Host "object itself IS on the remote now, just without that tag name attached." -ForegroundColor Yellow
