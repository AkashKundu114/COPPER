# ==============================================================================
# C.O.P.P.E.R. — Disable Windows Desktop Auto-Start
# Removes the Electron Desktop Application from automatically launching on PC boot / laptop open
# ==============================================================================

$copperRoot = "D:\C.O.P.P.E.R"
$startupFolder = [System.IO.Path]::Combine($env:APPDATA, "Microsoft\Windows\Start Menu\Programs\Startup")
$shortcutPath = [System.IO.Path]::Combine($startupFolder, "COPPER AI Guardian.lnk")
$registryPath = "HKCU:\Software\Microsoft\Windows\CurrentVersion\Run"
$registryName = "COPPER_Desktop_Guardian"
$taskName = "COPPER_Desktop_AutoLaunch"

Write-Host "==================================================================" -ForegroundColor Cyan
Write-Host "       REMOVING C.O.P.P.E.R. ELECTRON DESKTOP AUTO-START          " -ForegroundColor Yellow
Write-Host "==================================================================" -ForegroundColor Cyan

# 1. Remove Windows Startup Folder Shortcut
if (Test-Path $shortcutPath) {
    Remove-Item -Path $shortcutPath -Force -ErrorAction SilentlyContinue
    Write-Host "[+] Removed Startup Shortcut: $shortcutPath" -ForegroundColor Green
} else {
    Write-Host "[*] No shortcut found in Startup folder." -ForegroundColor Gray
}

# 2. Remove Windows Registry Run Key
$prop = Get-ItemProperty -Path $registryPath -Name $registryName -ErrorAction SilentlyContinue
if ($prop) {
    Remove-ItemProperty -Path $registryPath -Name $registryName -ErrorAction SilentlyContinue
    Write-Host "[+] Removed Windows Registry Run Key: $registryName" -ForegroundColor Green
} else {
    Write-Host "[*] No registry Run key found." -ForegroundColor Gray
}

# 3. Unregister Windows Task Scheduler Logon Task
try {
    $task = Get-ScheduledTask -TaskName $taskName -ErrorAction SilentlyContinue
    if ($task) {
        Unregister-ScheduledTask -TaskName $taskName -Confirm:$false -ErrorAction SilentlyContinue | Out-Null
        Write-Host "[+] Removed Scheduled Task: $taskName" -ForegroundColor Green
    } else {
        Write-Host "[*] No scheduled task found." -ForegroundColor Gray
    }
} catch {
    Write-Host "[*] Task Scheduler check completed." -ForegroundColor Gray
}

Write-Host "`n==================================================================" -ForegroundColor Cyan
Write-Host "[SUCCESS] C.O.P.P.E.R. auto-start on laptop open/boot has been DISABLED!" -ForegroundColor Green
Write-Host "          The app will now only launch when you explicitly start it." -ForegroundColor Cyan
Write-Host "==================================================================" -ForegroundColor Cyan
