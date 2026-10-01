Set WshShell = CreateObject("WScript.Shell")
Set FSO = CreateObject("Scripting.FileSystemObject")

' Get repo root directory dynamically (two levels above scripts\windows\)
ScriptDir = FSO.GetParentFolderName(WScript.ScriptFullName)
ScriptsDir = FSO.GetParentFolderName(ScriptDir)
RootDir = FSO.GetParentFolderName(ScriptsDir)

' Detect Python executable (venv or system)
PythonExe = "python"
If FSO.FileExists(RootDir & "\backend\.venv\Scripts\python.exe") Then
    PythonExe = """" & RootDir & "\backend\.venv\Scripts\python.exe"""
ElseIf FSO.FileExists(RootDir & "\.venv\Scripts\python.exe") Then
    PythonExe = """" & RootDir & "\.venv\Scripts\python.exe"""
End If

' 1. Start Python FastAPI Backend silently in the background
WshShell.Run "cmd /c ""cd /d " & RootDir & " && " & PythonExe & " -m uvicorn app.main:app --app-dir backend --host 127.0.0.1 --port 8000""", 0, False

' 2. Wait for backend initialization
WScript.Sleep 3000

' 3. Launch the C.O.P.P.E.R. Electron Standalone Desktop Application
WshShell.Run "cmd /c ""cd /d " & RootDir & "\frontend && npm.cmd run desktop""", 0, False