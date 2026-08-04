# 06-read-tree.ps1
# Tests: ugit read-tree <tree-oid>
# NOTE: per cli.py, `read_tree(args)` calls base.read_tree(args.tree) with
# update_working defaulting to False -> this only rewrites the INDEX, not the
# working directory. This script checks that specific (sometimes surprising)
# behaviour rather than assuming it repopulates files on disk.

$ErrorActionPreference = "Stop"
$dir = "test-read-tree"

Write-Host "`n=== ugit read-tree ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"version 1" | Out-File -Encoding ascii file.txt
ugit add file.txt
$treeOid = ugit write-tree
Write-Host "  tree oid = $treeOid"

# Change the index to something else (simulate by adding a new file)
"another file" | Out-File -Encoding ascii other.txt
ugit add other.txt

Write-Host "`n--- Index before read-tree ---"
Get-Content .ugit/index -Raw

ugit read-tree $treeOid

Write-Host "`n--- Index after read-tree (should match the tree, i.e. only file.txt) ---"
$index = Get-Content .ugit/index -Raw | ConvertFrom-Json
Get-Content .ugit/index -Raw

if (($index.PSObject.Properties.Name -contains "file.txt") -and
    ($index.PSObject.Properties.Name -notcontains "other.txt")) {
    Write-Host "  [PASS] Index now matches the read tree (other.txt dropped)" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Index does not match expected tree contents" -ForegroundColor Red
}

if (Test-Path "other.txt") {
    Write-Host "  [INFO] other.txt still exists on disk (expected: read-tree via CLI does not update the working directory)" -ForegroundColor Yellow
} else {
    Write-Host "  [INFO] other.txt was removed from disk" -ForegroundColor Yellow
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
