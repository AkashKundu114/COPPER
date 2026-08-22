Set WshShell = CreateObject("WScript.Shell")

' 1. Start Python FastAPI Backend silently in the background
WshShell.Run "cmd /c ""cd /d D:\C.O.P.P.E.R\backend & python -m uvicorn app.main:app --host 127.0.0.1 --port 8000""", 0, False

' 2. Wait for backend initialization
WScript.Sleep 2000

' 3. Launch the C.O.P.P.E.R. Electron Standalone Desktop Application (No browser)
WshShell.Run "cmd /c ""cd /d D:\C.O.P.P.E.R\frontend & npm run desktop""", 0, False