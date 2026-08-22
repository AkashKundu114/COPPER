@echo off
title C.O.P.P.E.R. Desktop Launcher
color 0b

echo ==================================================================
echo          C.O.P.P.E.R. ELECTRON DESKTOP DEV STARTUP                 
echo ==================================================================

cd /d "%~dp0..\.."

echo [*] Launching Backend Server (127.0.0.1:8000)...
start "COPPER Backend" cmd /k "python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"

echo [*] Launching Electron Desktop Application...
start "COPPER Electron Desktop" cmd /k "cd frontend && npm run desktop"

echo.
echo [+] Desktop App & Backend initiated. No web browser required.
echo ==================================================================
