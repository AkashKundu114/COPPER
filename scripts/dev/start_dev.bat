@echo off
title C.O.P.P.E.R. Desktop Launcher
color 0b

echo ==================================================================
echo          C.O.P.P.E.R. NATIVE DESKTOP DEV STARTUP                 
echo ==================================================================

cd /d "%~dp0..\.."

:: 1. Detect Python with uvicorn available
set "PYTHON_EXE=python"
if exist "backend\.venv\Scripts\python.exe" (
    backend\.venv\Scripts\python.exe -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%~dp0..\..\backend\.venv\Scripts\python.exe"
    )
)
if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%~dp0..\..\.venv\Scripts\python.exe"
    )
)

echo [*] Launching Backend Server (127.0.0.1:8000)...
start "COPPER Backend" cmd /k ""%PYTHON_EXE%" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

echo [*] Launching Frontend Development Server (localhost:5173)...
start "COPPER Frontend" cmd /k "cd frontend && npm.cmd run dev"

echo [*] Opening Standalone Desktop Window...
ping 127.0.0.1 -n 4 >nul

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

