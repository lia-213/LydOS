# 08-log.ps1
# Tests: ugit log [<oid>]

$ErrorActionPreference = "Stop"
$dir = "test-log"

Write-Host "`n=== ugit log ===" -ForegroundColor Cyan
Remove-Item -Recurse -Force $dir -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $dir | Out-Null
Push-Location $dir

ugit init
"1" | Out-File -Encoding ascii a.txt
ugit add a.txt
$c1 = ugit commit -m "commit one"

"2" | Out-File -Encoding ascii b.txt
ugit add b.txt
$c2 = ugit commit -m "commit two"

"3" | Out-File -Encoding ascii c.txt
ugit add c.txt
$c3 = ugit commit -m "commit three"

Write-Host "`n--- ugit log (defaults to @ / HEAD) ---"
$output = ugit log
Write-Host $output

$allThreePresent = ($output -match [regex]::Escape($c1)) -and
                    ($output -match [regex]::Escape($c2)) -and
                    ($output -match [regex]::Escape($c3))
if ($allThreePresent) {
    Write-Host "  [PASS] All three commits appear in log output" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] At least one commit missing from log" -ForegroundColor Red
}

if ($output -match "\(HEAD, refs.heads.master\)") {
    Write-Host "  [PASS] HEAD and master ref annotations shown on latest commit" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Ref annotations missing/unexpected" -ForegroundColor Red
}

Write-Host "`n--- ugit log <specific oid> (should only show that commit and its ancestors) ---"
$output2 = ugit log $c1
Write-Host $output2
if (($output2 -match [regex]::Escape($c1)) -and ($output2 -notmatch [regex]::Escape($c3))) {
    Write-Host "  [PASS] Logging from an older commit excludes its descendants" -ForegroundColor Green
} else {
    Write-Host "  [FAIL] Unexpected commits present when logging from $c1" -ForegroundColor Red
}

Pop-Location
Write-Host "`n=== Done ===" -ForegroundColor Cyan
