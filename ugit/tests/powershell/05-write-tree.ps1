# 05-write-tree.ps1
# Tests: ugit write-tree

$ErrorActionPreference = "Stop"
$dir = "test-write-tree"

Write-Host "`n=== ugit write-tree ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"root file" | Out-File -Encoding ascii root.txt
New-Item -ItemType Directory -Path sub | Out-Null
"nested file" | Out-File -Encoding ascii sub/nested.txt
ugit add root.txt sub

$treeOid = ugit write-tree
Write-Host "  tree oid = $treeOid"

if ($treeOid.Length -eq 64) {
    Write-Host "  [PASS] write-tree returned a 64-char OID" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Unexpected OID format" -ForegroundColor Red
}

$objectPath = ".ugit/objects/$treeOid"
if (Test-Path $objectPath) {
    Write-Host "  [PASS] Tree object written to disk" -ForegroundColor Green
    $raw = Get-Content $objectPath -Raw
    Write-Host "  raw object bytes (should start with 'tree' + null byte then entries):"
    Write-Host "    $raw"
} else {
    Write-Host "  [FAIL] Tree object missing on disk" -ForegroundColor Red
}

# Calling write-tree again with no index changes should produce the SAME oid (content-addressed)
$treeOid2 = ugit write-tree
if ($treeOid -eq $treeOid2) {
    Write-Host "  [PASS] Unchanged index -> identical tree OID on repeat call" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Tree OID changed with no index changes: $treeOid vs $treeOid2" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
