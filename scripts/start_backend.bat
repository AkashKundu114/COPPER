@echo off
title C.O.P.P.E.R. Backend
color 0a

echo ==================================================================
echo          C.O.P.P.E.R. - BACKEND FASTAPI SERVICE (PORT 8000)      
echo ==================================================================

cd /d "%~dp0.."

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

echo [*] Starting FastAPI Backend on 127.0.0.1:8000 using %PYTHON_EXE% ...
"%PYTHON_EXE%" -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000 --reload
