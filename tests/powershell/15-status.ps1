# 15-status.ps1
# Tests: ugit status

$ErrorActionPreference = "Stop"
$dir = "test-status"

Write-Host "`n=== ugit status ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1"

Write-Host "`n--- Status on a clean repo (should show branch, no pending changes) ---"
$out1 = ugit status
Write-Host $out1
if ($out1 -match "On branch master") {
    Write-Host "  [PASS] Correctly reports current branch" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Branch line missing/wrong" -ForegroundColor Red
}

Write-Host "`n--- Staging a new file (should show under 'Changes to be committed') ---"
"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$out2 = ugit status
Write-Host $out2
if ($out2 -match "new file: b.txt") {
    Write-Host "  [PASS] Staged new file shown as 'new file'" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Staged new file not reported correctly" -ForegroundColor Red
}

Write-Host "`n--- Modifying a tracked file WITHOUT staging (should show under 'not staged') ---"
"a modified" | Out-File -Encoding ascii a.txt
$out3 = ugit status
Write-Host $out3
if ($out3 -match "modified: a.txt") {
    Write-Host "  [PASS] Unstaged modification correctly reported" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Unstaged modification not reported correctly" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
