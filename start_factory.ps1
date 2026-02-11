# start_factory.ps1 - SOTA Clean Startup Script
# Purpose: Kill zombies on port 8002 and start the Dark App Factory Dashboard

$PORT = 8002
$SERVER_DIR = Join-Path $PSScriptRoot "web"

Write-Host "--- Dark App Factory: Industrial Startup Protocol ---" -ForegroundColor Blue

# 1. Kill Zombies
Write-Host "Searching for zombies on port $PORT..." -ForegroundColor Cyan
$zombieProcesses = Get-NetTCPConnection -LocalPort $PORT -ErrorAction SilentlyContinue | Where-Object { $_.State -eq 'Listen' }

if ($zombieProcesses) {
    Write-Host "Zombies detected! Commencing termination..." -ForegroundColor yellow
    foreach ($proc in $zombieProcesses) {
        $zpid = $proc.OwningProcess
        Write-Host "Terminating PID: $zpid" -ForegroundColor Red
        try {
            Stop-Process -Id $zpid -Force -ErrorAction SilentlyContinue
            Write-Host "PID $zpid successfully neutralized." -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to neutralize PID $zpid. (Access Denied?)" -ForegroundColor Red
        }
    }
}
else {
    Write-Host "No zombies detected. Port $PORT is clear." -ForegroundColor Green
}

# 2. Start Dashboard
Write-Host "Launching SOTA Dashboard from $SERVER_DIR..." -ForegroundColor Cyan
$env:PYTHONPATH = $PSScriptRoot
Set-Location $SERVER_DIR
# Use Start-Process to avoid blocking the script if needed, or run directly
python server.py
