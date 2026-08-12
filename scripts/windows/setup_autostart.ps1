# ==============================================================================
# COPPER — Windows Startup Installer Script
# Configures COPPER AI Guardian to start automatically on Windows boot
# ==============================================================================

$copperRoot = "D:\C.O.P.P.E.R"
$startupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$vbsPath = [System.IO.Path]::Combine($copperRoot, "scripts\windows\launch_copper.vbs")
$shortcutPath = [System.IO.Path]::Combine($startupFolder, "COPPER AI Guardian.lnk")

# 1. Create launch_copper.vbs background runner
$cmdBackend = 'cmd /c "cd /d D:\C.O.P.P.E.R\backend & python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"'
$cmdFrontend = 'cmd /c "cd /d D:\C.O.P.P.E.R\frontend & npm run dev"'

$vbsContent = "Set WshShell = CreateObject(`"WScript.Shell`")" + "`r`n" +
              "WshShell.Run `"$cmdBackend`", 0, False" + "`r`n" +
              "WScript.Sleep 2000" + "`r`n" +
              "WshShell.Run `"$cmdFrontend`", 0, False"

[System.IO.File]::WriteAllText($vbsPath, $vbsContent)
Write-Host "[OK] Created background launcher VBS: $vbsPath"

# 2. Create Windows Startup Folder Shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$vbsPath`""
$Shortcut.WorkingDirectory = $copperRoot
$Shortcut.Description = "COPPER Personal AI Guardian Operating System"
$Shortcut.Save()

Write-Host "[OK] Created Windows Startup Shortcut: $shortcutPath"

# 3. Register in Windows Registry CurrentVersion\Run
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $registryPath -Name "COPPER_Guardian" -Value "wscript.exe `"$vbsPath`""
Write-Host "[OK] Registered Windows Registry Startup Key: COPPER_Guardian"

Write-Host "SUCCESS: COPPER desktop application will now auto-start on Windows startup!"
