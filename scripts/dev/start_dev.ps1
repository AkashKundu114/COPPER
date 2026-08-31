# ──────────────────────────────────────────────────────────────────────────────
# C.O.P.P.E.R. Local Electron Desktop Environment Launcher (PowerShell)
# ──────────────────────────────────────────────────────────────────────────────

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "         C.O.P.P.E.R. ELECTRON DESKTOP STARTUP                   " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

$ROOT_DIR = (Get-Item $PSScriptRoot).Parent.Parent.FullName
Set-Location $ROOT_DIR

# 1. Check Python Virtual Environment / PATH
$PYTHON_CMD = "python"
if (Test-Path "$ROOT_DIR\.venv\Scripts\python.exe") {
    $PYTHON_CMD = "$ROOT_DIR\.venv\Scripts\python.exe"
}

Write-Host "[*] Python Environment: $PYTHON_CMD" -ForegroundColor Yellow

# 2. Start Backend FastAPI Server
Write-Host "[*] Launching FastAPI Backend on 127.0.0.1:8000 ..." -ForegroundColor Green
$backendProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR'; $PYTHON_CMD -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload" -PassThru

# 3. Start Electron Desktop Application
Write-Host "[*] Launching C.O.P.P.E.R. Electron Desktop App ..." -ForegroundColor Green
$desktopProcess = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$ROOT_DIR\frontend'; npm run desktop" -PassThru

Write-Host "`n[+] C.O.P.P.E.R. Electron Desktop App initiated! No web browser used." -ForegroundColor Cyan
