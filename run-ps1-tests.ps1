# run-ps1-tests.ps1
#
# Copies the PowerShell CLI test scripts from the tracked repo (l_git) into
# the untracked sandbox, then runs them there. This is the "copy + run in
# one step" script -- steps 1 (copy) and running (step 2) combined, so a
# buggy ugit checkout/add/etc. can never touch the source tree in l_git.
#
# Edit the two paths below if your folders live somewhere else.

$ErrorActionPreference = "Stop"

$SourceDir = "C:\Users\lydbo\l_git\tests\powershell"
$SandboxDir = "C:\Users\lydbo\ugit-sandbox\ugit-scripts"

Write-Host "`n=== Copying PowerShell test scripts to sandbox ===" -ForegroundColor Cyan

if (-not (Test-Path $SourceDir)) {
    Write-Host "  [FAIL] Source folder not found: $SourceDir" -ForegroundColor Red
    Write-Host "  (Have you run the one-time setup step from the README yet?)" -ForegroundColor Yellow
    exit 1
}

if (-not (Test-Path $SandboxDir)) {
    Write-Host "  Sandbox folder doesn't exist yet -- creating it: $SandboxDir" -ForegroundColor Yellow
    New-Item -ItemType Directory -Path $SandboxDir -Force | Out-Null
}

Copy-Item "$SourceDir\*.ps1" $SandboxDir -Force
Write-Host "  [PASS] Scripts copied to $SandboxDir" -ForegroundColor Green

# Newly copied files may be flagged with Windows' "Mark of the Web" if the
# source files were themselves downloaded at some point -- unblock them so
# PowerShell's execution policy doesn't refuse to run them.
Get-ChildItem "$SandboxDir\*.ps1" | Unblock-File

Write-Host "`n=== Running tests from sandbox ===" -ForegroundColor Cyan
Push-Location $SandboxDir

$runAll = Join-Path $SandboxDir "00-run-all.ps1"
if (Test-Path $runAll) {
    & $runAll
} else {
    Write-Host "  [FAIL] 00-run-all.ps1 not found in $SandboxDir" -ForegroundColor Red
}

Pop-Location

Write-Host "`n=== Done. Ran from sandbox, source tree untouched. ===" -ForegroundColor Cyan
