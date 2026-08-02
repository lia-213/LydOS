# 02-hash-object.ps1
# Tests: ugit hash-object <file>

$ErrorActionPreference = "Stop"
$dir = "test-hash-object"

Write-Host "`n=== ugit hash-object ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"Hello World" | Out-File -Encoding ascii hello.txt

$oid = ugit hash-object hello.txt
Write-Host "  oid = $oid"

if ($oid.Length -eq 64) {
    Write-Host "  [PASS] OID looks like a 64-char sha256 hex digest" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] OID has unexpected length: $($oid.Length)" -ForegroundColor Red
}

$objectPath = ".ugit\objects\$oid"
if (Test-Path $objectPath) {
    Write-Host "  [PASS] Object file written to $objectPath" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Object file missing at $objectPath" -ForegroundColor Red
}

# Hashing the same content again should give the same oid (content-addressing)
$oid2 = ugit hash-object hello.txt
if ($oid -eq $oid2) {
    Write-Host "  [PASS] Hashing identical content twice gives the same OID" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] OIDs differ across runs: $oid vs $oid2" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
