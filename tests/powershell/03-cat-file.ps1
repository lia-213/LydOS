# 03-cat-file.ps1
# Tests: ugit cat-file <oid>

$ErrorActionPreference = "Stop"
$dir = "test-cat-file"

Write-Host "`n=== ugit cat-file ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"Hello World" | Out-File -Encoding ascii hello.txt
$oid = ugit hash-object hello.txt

$content = ugit cat-file $oid
Write-Host "  cat-file output: $content"

if ($content.Trim() -eq "Hello World") {
    Write-Host "  [PASS] cat-file returned original blob content" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] cat-file content mismatch: got '$content'" -ForegroundColor Red
}

# cat-file with '@' should resolve HEAD -> commit object (only valid after a commit exists)
ugit add hello.txt
$commitOid = ugit commit -m "first commit"
Write-Host "`n--- cat-file @ (resolves to HEAD commit object) ---"
$headContent = ugit cat-file "@"
Write-Host $headContent

if ($headContent -match "^tree ") {
    Write-Host "  [PASS] cat-file @ shows a commit object starting with 'tree '" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Unexpected commit object content" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
