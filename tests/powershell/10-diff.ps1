# 10-diff.ps1
# Tests: ugit diff [--cached] [<commit>]
#
# NOTE / HEADS UP: in the pasted cli.py, _diff() builds `result` via
# diff.diff_trees(...) and does `return result` -- but never calls print().
# Since cli.main() just does `args.func(args)` and discards the return value,
# `ugit diff` currently prints NOTHING to the terminal no matter what changed.
# This script will surface that directly so you can decide whether to add
# `print(result)` in _diff() (mirroring how commit/write_tree do print(...)).

$ErrorActionPreference = "Stop"
$dir = "test-diff"

Write-Host "`n=== ugit diff ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"line one`n" | Out-File -Encoding ascii file.txt -NoNewline
ugit add file.txt
$c1 = ugit commit -m "initial commit"

# Unstaged change: working dir differs from index
"line one`nline two`n" | Out-File -Encoding ascii file.txt -NoNewline

Write-Host "`n--- ugit diff (index vs working dir, unstaged change) ---"
$output = ugit diff
Write-Host "RAW OUTPUT: [$output]"
if ([string]::IsNullOrWhiteSpace($output)) {
    Write-Host "  [INFO] No output printed. This matches the suspected missing print() bug in cli.py's _diff()." -ForegroundColor Yellow
} else {
    Write-Host "  [PASS] diff printed something" -ForegroundColor Green
}

# Stage the change, then check --cached (index vs HEAD)
ugit add file.txt
Write-Host "`n--- ugit diff --cached (HEAD vs index, staged change) ---"
$output2 = ugit diff --cached
Write-Host "RAW OUTPUT: [$output2]"
if ([string]::IsNullOrWhiteSpace($output2)) {
    Write-Host "  [INFO] No output printed here either — same missing-print() suspicion." -ForegroundColor Yellow
} else {
    Write-Host "  [PASS] diff --cached printed something" -ForegroundColor Green
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
Write-Host "If both outputs above were empty, check cli.py's _diff() — it computes" -ForegroundColor Yellow
Write-Host "'result' via diff.diff_trees(...) but returns it instead of printing it." -ForegroundColor Yellow
