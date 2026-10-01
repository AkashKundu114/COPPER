@echo off
title C.O.P.P.E.R. Launcher
color 0b

echo ==================================================================
echo          C.O.P.P.E.R. - COGNITIVE DESKTOP ENVIRONMENT            
echo ==================================================================

cd /d "%~dp0.."

:: 1. Detect Python with uvicorn available
set "PYTHON_EXE=python"
if exist "%~dp0..\backend\.venv\Scripts\python.exe" (
    "%~dp0..\backend\.venv\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%~dp0..\backend\.venv\Scripts\python.exe"
    )
)
if exist "%~dp0..\.venv\Scripts\python.exe" (
    "%~dp0..\.venv\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
    )
)

echo [*] Using Python: %PYTHON_EXE%

:: 2. Launch Backend Server in new window
echo [*] Launching C.O.P.P.E.R. Backend on 127.0.0.1:8000 ...
start "COPPER Backend" cmd /k "cd /d ""%~dp0.."" && ""%PYTHON_EXE%"" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload"

:: 3. Launch Frontend Development Server in new window
echo [*] Launching C.O.P.P.E.R. Frontend on localhost:5173 ...
start "COPPER Frontend" cmd /k "cd /d ""%~dp0..\frontend"" && npm.cmd run dev"

:: 4. Wait for services to spin up
echo [*] Waiting for services to initialize...
ping 127.0.0.1 -n 4 >nul

:: 5. Launch Standalone App Window (Chrome / Edge / Default Browser)
if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5173 --window-size=1360,860 --user-data-dir="%LOCALAPPDATA%\COPPER\ChromeProfile"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:5173 --window-size=1360,860 --user-data-dir="%LOCALAPPDATA%\COPPER\EdgeProfile"
) else (
    start http://localhost:5173
)

echo.
echo [+] C.O.P.P.E.R. started successfully.
echo [+] To stop all services, run 'scripts\stop_copper.bat'.
echo ==================================================================
