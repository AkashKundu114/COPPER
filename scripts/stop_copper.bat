@echo off
title Stop C.O.P.P.E.R.
color 0c

echo ==================================================================
echo          STOPPING C.O.P.P.E.R. SERVICES                           
echo ==================================================================

echo [*] Stopping backend processes on port 8000 ...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8000" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo [*] Stopping frontend processes on port 5173 ...
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":5173" ^| findstr "LISTENING"') do (
    taskkill /f /pid %%a >nul 2>&1
)

echo [*] Closing dedicated terminal windows...
taskkill /f /fi "WINDOWTITLE eq COPPER Backend*" >nul 2>&1
taskkill /f /fi "WINDOWTITLE eq COPPER Frontend*" >nul 2>&1

echo.
echo [+] All C.O.P.P.E.R. services stopped.
echo ==================================================================
ping 127.0.0.1 -n 3 >nul
