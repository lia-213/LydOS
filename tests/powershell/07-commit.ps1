# 07-commit.ps1
# Tests: ugit commit -m "message"

$ErrorActionPreference = "Stop"
$dir = "test-commit"

Write-Host "`n=== ugit commit ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"first" | Out-File -Encoding ascii file.txt
ugit add file.txt
$commit1 = ugit commit -m "first commit"
Write-Host "  commit1 = $commit1"

if (Test-Path ".ugit\objects\$commit1") {
    Write-Host "  [PASS] Commit object written to disk" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Commit object missing" -ForegroundColor Red
}

$headValue = Get-Content ".ugit\refs\heads\master" -Raw
if ($headValue.Trim() -eq $commit1) {
    Write-Host "  [PASS] refs/heads/master points at the new commit" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] master ref mismatch: $headValue vs $commit1" -ForegroundColor Red
}

# First commit should have NO parent line
$commitBody = ugit cat-file $commit1
if ($commitBody -notmatch "parent") {
    Write-Host "  [PASS] First commit has no parent" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] First commit unexpectedly has a parent" -ForegroundColor Red
}

# Second commit SHOULD have a parent line pointing at commit1
"second" | Out-File -Encoding ascii file2.txt
ugit add file2.txt
$commit2 = ugit commit -m "second commit"
$commitBody2 = ugit cat-file $commit2
Write-Host "`n--- Second commit object ---"
Write-Host $commitBody2

if ($commitBody2 -match "parent $commit1") {
    Write-Host "  [PASS] Second commit correctly references first as parent" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Second commit's parent line is wrong or missing" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
