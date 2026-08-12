Set WshShell = CreateObject("WScript.Shell")
WshShell.Run "cmd /c "cd /d D:\C.O.P.P.E.R\backend & python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"", 0, False
WScript.Sleep 2000
WshShell.Run "cmd /c "cd /d D:\C.O.P.P.E.R\frontend & npm run dev"", 0, False
WScript.Sleep 1500
WshShell.Run "cmd /c "start msedge --app=http://localhost:5173 --window-name=""COPPER AI Guardian"""", 0, False