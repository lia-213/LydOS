# ugit-checkout-test.ps1
# Run this from inside your sandbox dir (e.g. C:\Users\lydbo\ugit-sandbox)

$ErrorActionPreference = "Stop"

function Assert-Exists($path, $desc) {
    if (Test-Path $path) {
        Write-Host "  [PASS] $desc ('$path' exists)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $desc ('$path' MISSING)" -ForegroundColor Red
    }
}

function Assert-NotExists($path, $desc) {
    if (-not (Test-Path $path)) {
        Write-Host "  [PASS] $desc ('$path' correctly absent)" -ForegroundColor Green
    } else {
        Write-Host "  [FAIL] $desc ('$path' should NOT exist)" -ForegroundColor Red
    }
}

# --- Clean slate ---
Write-Host "`n=== Setting up clean test dir ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force .ugit -ErrorAction SilentlyContinue
Remove-Item -Force *.txt -ErrorAction SilentlyContinue
Remove-Item -Recurse -Force src -ErrorAction SilentlyContinue

ugit init

# --- Commit 1: tracked1.txt only ---
Write-Host "`n=== Commit 1: add tracked1.txt ===" -ForegroundColor Cyan
"tracked file 1" | Out-File -Encoding ascii tracked1.txt
ugit add tracked1.txt
$commit1 = ugit commit -m "commit 1"
Write-Host "commit1 = $commit1"

# --- Create an UNTRACKED file (never added, should survive everything) ---
Write-Host "`n=== Creating untracked file (never git-added) ===" -ForegroundColor Cyan
"this should never be touched" | Out-File -Encoding ascii untracked.txt

# --- Commit 2: add tracked2.txt (in a subdir, to test dir handling too) ---
Write-Host "`n=== Commit 2: add src/tracked2.txt ===" -ForegroundColor Cyan
New-Item -ItemType Directory -Path src -Force | Out-Null
"tracked file 2" | Out-File -Encoding ascii src/tracked2.txt
ugit add tracked1.txt src/tracked2.txt
$commit2 = ugit commit -m "commit 2"
Write-Host "commit2 = $commit2"

# --- Sanity check: everything present right now ---
Write-Host "`n=== State after commit 2 (before any checkout) ===" -ForegroundColor Cyan
Assert-Exists "tracked1.txt" "tracked1.txt present"
Assert-Exists "src/tracked2.txt" "src/tracked2.txt present"
Assert-Exists "untracked.txt" "untracked.txt present"

# --- Checkout commit 1: tracked2.txt should disappear, untracked.txt must survive ---
Write-Host "`n=== Checking out commit 1 ===" -ForegroundColor Cyan
ugit checkout $commit1

Assert-Exists    "tracked1.txt"     "tracked1.txt still present at commit 1"
Assert-NotExists "src/tracked2.txt" "src/tracked2.txt removed (wasn't part of commit 1)"
Assert-Exists    "untracked.txt"    "untracked.txt SURVIVED checkout (this is the bug fix)"

# --- Checkout commit 2 again: tracked2.txt should come back, untracked.txt still there ---
Write-Host "`n=== Checking out commit 2 ===" -ForegroundColor Cyan
ugit checkout $commit2

Assert-Exists "tracked1.txt"     "tracked1.txt present at commit 2"
Assert-Exists "src/tracked2.txt" "src/tracked2.txt restored at commit 2"
Assert-Exists "untracked.txt"    "untracked.txt STILL survived (checked twice now)"

Write-Host "`n=== Test complete ===" -ForegroundColor Cyan

ugit k