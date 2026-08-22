# ──────────────────────────────────────────────────────────────────────────────
# C.O.P.P.E.R. Automated Pytest Test Runner
# ──────────────────────────────────────────────────────────────────────────────

$ROOT_DIR = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $ROOT_DIR

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "             C.O.P.P.E.R. PYTEST SUITE EXECUTION                  " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

python -m pytest tests/ -v --tb=short
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "`n[+] All tests passed successfully!" -ForegroundColor Green
} else {
    Write-Host "`n[-] Some tests failed with exit code $exitCode." -ForegroundColor Red
}

exit $exitCode
