@echo off
title C.O.P.P.E.R. Frontend
color 0e

echo ==================================================================
echo          C.O.P.P.E.R. - FRONTEND DEV SERVER (PORT 5173)         
echo ==================================================================

cd /d "%~dp0..\frontend"

echo [*] Starting Vite Frontend on localhost:5173 ...
npm.cmd run dev
