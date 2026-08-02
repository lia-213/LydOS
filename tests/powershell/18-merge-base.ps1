# 18-merge-base.ps1
# Tests: ugit merge-base <commit1> <commit2>

$ErrorActionPreference = "Stop"
$dir = "test-merge-base"

Write-Host "`n=== ugit merge-base ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$base = ugit commit -m "common ancestor"
Write-Host "  base = $base"

ugit branch feature
ugit checkout feature
"feature file" | Out-File -Encoding ascii feature.txt
ugit add feature.txt
$featureCommit = ugit commit -m "feature commit"

ugit checkout master
"master file" | Out-File -Encoding ascii master.txt
ugit add master.txt
$masterCommit = ugit commit -m "master commit"

Write-Host "`n--- Finding merge base of diverged master/feature commits ---"
$result = ugit merge-base $masterCommit $featureCommit
Write-Host "  merge-base = $result (expected $base)"

if ($result.Trim() -eq $base) {
    Write-Host "  [PASS] merge-base correctly identifies the common ancestor" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] merge-base returned an unexpected commit" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
