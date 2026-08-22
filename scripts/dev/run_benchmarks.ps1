# ──────────────────────────────────────────────────────────────────────────────
# C.O.P.P.E.R. Evaluation & Routing Benchmark Runner
# ──────────────────────────────────────────────────────────────────────────────

$ROOT_DIR = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $ROOT_DIR

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "         C.O.P.P.E.R. BENCHMARK & EVALUATION SUITE                " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

python backend/eval/benchmark.py
$exitCode = $LASTEXITCODE

exit $exitCode
