# ──────────────────────────────────────────────────────────────────────────────
# C.O.P.P.E.R. Process Teardown & Graceful Shutdown (Windows)
# ──────────────────────────────────────────────────────────────────────────────

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "           STOPPING C.O.P.P.E.R. BACKGROUND SERVICES              " -ForegroundColor Red
Write-Host "==================================================================" -ForegroundColor Cyan

# Terminate Python Uvicorn instances running on port 8000
$uvicornPids = (Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue).OwningProcess
if ($uvicornPids) {
    foreach ($p in $uvicornPids) {
        Write-Host "[*] Terminating Backend Process PID: $p" -ForegroundColor Yellow
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    }
}

# Terminate Vite dev server running on port 5173
$vitePids = (Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue).OwningProcess
if ($vitePids) {
    foreach ($p in $vitePids) {
        Write-Host "[*] Terminating Frontend Process PID: $p" -ForegroundColor Yellow
        Stop-Process -Id $p -Force -ErrorAction SilentlyContinue
    }
}

Write-Host "[+] All C.O.P.P.E.R. services stopped." -ForegroundColor Green
