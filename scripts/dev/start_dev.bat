@echo off
title C.O.P.P.E.R. Desktop Launcher
color 0b

echo ==================================================================
echo          C.O.P.P.E.R. NATIVE DESKTOP DEV STARTUP                 
echo ==================================================================

cd /d "%~dp0..\.."

echo [*] Launching Backend Server (127.0.0.1:8000)...
start "COPPER Backend" cmd /k "python -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000"

echo [*] Launching Frontend Development Server (localhost:5173)...
start "COPPER Frontend" cmd /k "cd frontend && npm run dev"

echo [*] Opening Standalone Desktop Window...
timeout /t 3 /nobreak >nul

if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5173 --window-size=1360,860 --user-data-dir="%LOCALAPPDATA%\COPPER\ChromeProfile"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:5173 --window-size=1360,860 --user-data-dir="%LOCALAPPDATA%\COPPER\EdgeProfile"
) else (
    start http://localhost:5173
)

echo.
echo [+] Desktop App & Backend initiated.
echo ==================================================================

