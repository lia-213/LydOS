# 14-k.ps1
# Tests: ugit k
#
# NOTE / HEADS UP: in the pasted cli.py, the Graphviz-found branch builds the
# subprocess args as `['dot, '-Tpng]` -- this is malformed (a stray quote makes
# it parse as "'dot, ' - Tpng", i.e. string minus an undefined name) and will
# raise a NameError/TypeError at runtime if Graphviz's `dot` IS found on PATH.
# Most machines won't have `dot` installed, so this script mainly exercises
# the fallback path: printing the DOT graph text and opening the web
# visualiser in a browser. If you DO have Graphviz installed, expect this to
# fail until that line is fixed to something like:
#   ['dot', '-Tpng']

$ErrorActionPreference = "Stop"
$dir = "test-k"

Write-Host "`n=== ugit k ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"a" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit 1"

"b" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit 2"

Write-Host "`n--- Running ugit k (watch for DOT graph text or a browser tab opening) ---"
try {
    ugit k
    Write-Host "  [PASS] ugit k ran without raising an exception" -ForegroundColor Green
} catch {
    Write-Host "  [FAIL] ugit k raised an error: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "  (If 'dot' is on your PATH, this is likely the malformed subprocess args bug noted above)" -ForegroundColor Yellow
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
