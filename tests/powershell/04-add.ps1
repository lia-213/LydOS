# 04-add.ps1
# Tests: ugit add <file> [<file> ...] and ugit add <directory>

$ErrorActionPreference = "Stop"
$dir = "test-add"

Write-Host "`n=== ugit add ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init

"root file" | Out-File -Encoding ascii root.txt
New-Item -ItemType Directory -Path sub | Out-Null
"nested file" | Out-File -Encoding ascii sub\nested.txt

Write-Host "`n--- Adding a single file ---"
ugit add root.txt
$index = Get-Content .ugit\index -Raw | ConvertFrom-Json
if ($index.PSObject.Properties.Name -contains "root.txt") {
    Write-Host "  [PASS] root.txt staged" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] root.txt not staged" -ForegroundColor Red
}

Write-Host "`n--- Adding a directory (recursive) ---"
ugit add sub
$index = Get-Content .ugit\index -Raw | ConvertFrom-Json
if ($index.PSObject.Properties.Name -contains "sub\nested.txt") {
    Write-Host "  [PASS] sub\nested.txt staged via directory add" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] sub\nested.txt not staged" -ForegroundColor Red
}

Write-Host "`n--- Adding multiple explicit filenames at once ---"
"another root file" | Out-File -Encoding ascii root2.txt
ugit add root.txt root2.txt
$index = Get-Content .ugit\index -Raw | ConvertFrom-Json
if (($index.PSObject.Properties.Name -contains "root.txt") -and ($index.PSObject.Properties.Name -contains "root2.txt")) {
    Write-Host "  [PASS] Multiple files staged in one call" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Multi-file add did not stage everything" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
