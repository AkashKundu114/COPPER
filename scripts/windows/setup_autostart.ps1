# ==============================================================================
# C.O.P.P.E.R. — Windows Desktop Auto-Start Installer
# Configures the Electron Desktop Application to automatically launch on PC boot
# ==============================================================================

$copperRoot = "D:\C.O.P.P.E.R"
$startupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$vbsPath = [System.IO.Path]::Combine($copperRoot, "scripts\windows\launch_copper.vbs")
$shortcutPath = [System.IO.Path]::Combine($startupFolder, "COPPER AI Guardian.lnk")

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "       CONFIGURING C.O.P.P.E.R. ELECTRON DESKTOP AUTO-START       " -ForegroundColor Green
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Verify VBS Launcher
if (-not (Test-Path $vbsPath)) {
    Write-Host "[-] Error: launch_copper.vbs not found at $vbsPath" -ForegroundColor Red
    exit 1
}

# 2. Create Windows Startup Folder Shortcut
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut($shortcutPath)
$Shortcut.TargetPath = "wscript.exe"
$Shortcut.Arguments = "`"$vbsPath`""
$Shortcut.WorkingDirectory = $copperRoot
$Shortcut.Description = "COPPER Autonomous AI Desktop Guardian"
$Shortcut.Save()

Write-Host "[+] Created Startup Shortcut: $shortcutPath" -ForegroundColor Green

# 3. Register in Windows Registry (HKCU Run Key) for instantaneous startup
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
Set-ItemProperty -Path $registryPath -Name "COPPER_Desktop_Guardian" -Value "wscript.exe `"$vbsPath`""
Write-Host "[+] Registered Windows Registry Run Key: COPPER_Desktop_Guardian" -ForegroundColor Green

# 4. Create Task Scheduler Logon Task for seamless background execution
$taskName = "COPPER_Desktop_AutoLaunch"
$action = New-ScheduledTaskAction -Execute "wscript.exe" -Argument "`"$vbsPath`"" -WorkingDirectory $copperRoot
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -ExecutionTimeLimit 0

try {
    Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
    Register-ScheduledTask -TaskName $taskName -Action $action -Trigger $trigger -Settings $settings -Description "Auto-starts COPPER Electron Desktop App on Windows login" | Out-Null
    Write-Host "[+] Registered Windows Task Scheduler Logon Task: $taskName" -ForegroundColor Green
} catch {
    Write-Host "[*] Task Scheduler registration skipped (admin rights optional, registry & startup folder active)" -ForegroundColor Yellow
}

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] C.O.P.P.E.R. Electron Desktop App is set to auto-start on PC boot!" -ForegroundColor Green
Write-Host "[INFO] Nothing will open in web browsers. All interactions stay inside Electron." -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
