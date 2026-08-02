# ugit-add-dot-test.ps1
# Run this from inside your sandbox dir (e.g. C:\Users\lydbo\ugit-sandbox)

$ErrorActionPreference = "Stop"

function Assert-InIndex($path, $index, $desc) {
    if ($index.PSObject.Properties.Name -contains $path) {
        Write-Host "  [PASS] $desc ('$path' IS staged)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $desc ('$path' NOT staged, should be)" -ForegroundColor Red
    }
}

function Assert-NotInIndex($path, $index, $desc) {
    if ($index.PSObject.Properties.Name -notcontains $path) {
        Write-Host "  [PASS] $desc ('$path' correctly NOT staged)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $desc ('$path' WAS staged, should NOT be)" -ForegroundColor Red
    }
}

# --- Clean slate ---
Write-Host "`n=== Setting up clean test dir ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force .ugit -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force root1.txt, root2.txt, sub, ignoreme.venv -ErrorAction SilentlyContinue

ugit init

# --- Create a mix of files: root-level, nested, and things that should be ignored ---
Write-Host "`n=== Creating test files ===" -ForegroundColor Cyan

"root file 1" | Out-File -Encoding ascii root1.txt
"root file 2" | Out-File -Encoding ascii root2.txt

New-Item -ItemType Directory -Path sub -Force | Out-Null
"nested file" | Out-File -Encoding ascii sub\nested.txt

New-Item -ItemType Directory -Path sub\deeper -Force | Out-Null
"deeply nested file" | Out-File -Encoding ascii sub\deeper\deep.txt

# Simulate a .venv-like ignored directory
New-Item -ItemType Directory -Path .venv -Force | Out-Null
"should be ignored" | Out-File -Encoding ascii .venv\fake_venv_file.txt

# --- Run ugit add . ---
Write-Host "`n=== Running 'ugit add .' ===" -ForegroundColor Cyan
ugit add .

# --- Inspect the index ---
Write-Host "`n=== Inspecting .ugit/index ===" -ForegroundColor Cyan
$indexRaw = Get-Content .ugit\index -Raw
Write-Host $indexRaw
$index = $indexRaw | ConvertFrom-Json

# --- Assertions ---
Write-Host "`n=== Checking results ===" -ForegroundColor Cyan
Assert-InIndex    "root1.txt"              $index "Root-level file staged"
Assert-InIndex    "root2.txt"              $index "Root-level file staged"
Assert-InIndex    "sub\nested.txt"         $index "Nested file staged"
Assert-InIndex    "sub\deeper\deep.txt"    $index "Deeply nested file staged"
Assert-NotInIndex ".venv\fake_venv_file.txt" $index "Ignored (.venv) file NOT staged"
Assert-NotInIndex ".ugit\index"            $index ".ugit internals NOT staged"

# --- Now commit and verify write_tree/checkout roundtrip works with this index ---
Write-Host "`n=== Commit and roundtrip check ===" -ForegroundColor Cyan
$commit1 = ugit commit -m "add dot test commit"
Write-Host "commit1 = $commit1"

Remove-Item root1.txt, root2.txt -Force
Remove-Item -Recurse -Force sub

ugit checkout $commit1

if ((Test-Path root1.txt) -and (Test-Path root2.txt) -and (Test-Path sub\nested.txt) -and (Test-Path sub\deeper\deep.txt)) {
    Write-Host "  [PASS] All files correctly restored via checkout after 'add .' + commit" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Some files missing after checkout - add . / write_tree may still be broken" -ForegroundColor Red
}

Write-Host "`n=== Test complete ===" -ForegroundColor Cyan