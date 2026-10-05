@echo off
title C.O.P.P.E.R. Backend
color 0a

echo ==================================================================
echo          C.O.P.P.E.R. - BACKEND FASTAPI SERVICE (PORT 8000)      
echo ==================================================================

cd /d "%~dp0.."

set "PYTHON_EXE="

:: 1. Check workspace virtual environments
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

:: 2. Check system Python and Py launcher
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

:: 3. Clear any stale process on port 8000
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo [*] Starting FastAPI Backend on 127.0.0.1:8000 using %PYTHON_EXE% ...
"%PYTHON_EXE%" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload

