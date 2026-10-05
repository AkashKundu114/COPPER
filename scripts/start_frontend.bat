@echo off
title C.O.P.P.E.R. Frontend
color 0e

echo ==================================================================
echo          C.O.P.P.E.R. - FRONTEND DEV SERVER (PORT 5173)         
echo ==================================================================

cd /d "%~dp0..\frontend"

:: Clear any stale process on port 5173
for /f "tokens=5" %%a in ('netstat -aon 2^>nul ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

:: Check if node_modules exists
if not exist "node_modules\" (
    echo [*] Installing frontend dependencies...
    call npm.cmd install
)

echo [*] Starting Vite Frontend on localhost:5173 ...
call npm.cmd run dev

