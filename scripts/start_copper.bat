@echo off
title C.O.P.P.E.R. Launcher
color 0b

echo ==================================================================
echo          C.O.P.P.E.R. - COGNITIVE DESKTOP ENVIRONMENT            
echo ==================================================================

cd /d "%~dp0.."

:: 1. Detect Python with uvicorn available
set "PYTHON_EXE="
if exist "%~dp0..\.venv\Scripts\python.exe" (
    "%~dp0..\.venv\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%~dp0..\.venv\Scripts\python.exe"
    )
)
if not defined PYTHON_EXE if exist "%~dp0..\backend\.venv\Scripts\python.exe" (
    "%~dp0..\backend\.venv\Scripts\python.exe" -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=%~dp0..\backend\.venv\Scripts\python.exe"
    )
)
if not defined PYTHON_EXE (
    python -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=python"
    )
)
if not defined PYTHON_EXE (
    py -c "import uvicorn" >nul 2>&1
    if not errorlevel 1 (
        set "PYTHON_EXE=py"
    )
)
if not defined PYTHON_EXE (
    if exist "%LOCALAPPDATA%\Python\bin\python.exe" (
        "%LOCALAPPDATA%\Python\bin\python.exe" -c "import uvicorn" >nul 2>&1
        if not errorlevel 1 (
            set "PYTHON_EXE=%LOCALAPPDATA%\Python\bin\python.exe"
        )
    )
)

if not defined PYTHON_EXE (
    echo [-] Error: Python runtime with 'uvicorn' was not found!
    echo [*] Please ensure Python 3.11+ is installed and run:
    echo     pip install -r backend\requirements.txt
    echo.
    pause
    exit /b 1
)

echo [*] Detected Python Runtime: %PYTHON_EXE%

:: 2. Clean up any stale instances on ports 8000 and 5173
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: 3. Launch Backend Server in dedicated window
echo [*] Launching C.O.P.P.E.R. Backend on 127.0.0.1:8000 ...
start "COPPER Backend" cmd /k "%~dp0start_backend.bat"

:: 4. Launch Frontend Development Server in dedicated window
echo [*] Launching C.O.P.P.E.R. Frontend on localhost:5173 ...
start "COPPER Frontend" cmd /k "%~dp0start_frontend.bat"

:: 5. Wait for frontend dev server to be responsive
echo [*] Waiting for services to initialize...
set /a ATTEMPTS=0
:wait_services
set /a ATTEMPTS+=1
ping 127.0.0.1 -n 2 >nul
curl.exe -s -f http://localhost:5173 >nul 2>&1
if not errorlevel 1 goto :services_ready
if %ATTEMPTS% geq 25 goto :services_ready
goto :wait_services


:services_ready
echo [+] Services initialized.

:: 6. Launch Desktop Environment
if exist "%~dp0..\frontend\node_modules\electron\dist\electron.exe" (
    echo [*] Launching Native Electron Desktop Window...
    start "" "%~dp0..\frontend\node_modules\electron\dist\electron.exe" "%~dp0..\frontend" --force_high_performance_gpu
) else if exist "C:\Program Files\Google\Chrome\Application\chrome.exe" (
    echo [*] Launching Standalone Chrome App Window...
    start "" "C:\Program Files\Google\Chrome\Application\chrome.exe" --app=http://localhost:5173 --window-size=1360,860 --user-data-dir="%LOCALAPPDATA%\COPPER\ChromeProfile"
) else if exist "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" (
    echo [*] Launching Standalone Edge App Window...
    start "" "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe" --app=http://localhost:5173 --window-size=1360,860 --user-data-dir="%LOCALAPPDATA%\COPPER\EdgeProfile"
) else (
    echo [*] Launching in Default Browser...
    start http://localhost:5173
)

echo.
echo ==================================================================
echo [+] C.O.P.P.E.R. started successfully!
echo [*] Backend API:       http://127.0.0.1:8000
echo [*] Swagger Docs:      http://127.0.0.1:8000/docs
echo [*] Frontend Web UI:   http://localhost:5173
echo [*] To stop all services cleanly, run: scripts\stop_copper.bat
echo ==================================================================

