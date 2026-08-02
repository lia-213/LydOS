# 09-show.ps1
# Tests: ugit show [<oid>]

$ErrorActionPreference = "Stop"
$dir = "test-show"

Write-Host "`n=== ugit show ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"line one`n" | Out-File -Encoding ascii file.txt -NoNewline
ugit add file.txt
$c1 = ugit commit -m "add file"

"line one`nline two`n" | Out-File -Encoding ascii file.txt -NoNewline
ugit add file.txt
$c2 = ugit commit -m "append line two"

Write-Host "`n--- ugit show (defaults to @ / HEAD) ---"
$output = ugit show
Write-Host $output

if ($output -match "commit $c2") {
    Write-Host "  [PASS] show displays the correct commit header" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Commit header missing/wrong" -ForegroundColor Red
}

if ($output -match "\+line two") {
    Write-Host "  [PASS] Diff shows 'line two' as an added line" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Expected diff content not found" -ForegroundColor Red
}

Write-Host "`n--- ugit show <first commit> (no parent -> diff against empty tree) ---"
$output2 = ugit show $c1
Write-Host $output2
if ($output2 -match "\+line one") {
    Write-Host "  [PASS] First commit's show output treats it as entirely new content" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Unexpected output for root commit" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
