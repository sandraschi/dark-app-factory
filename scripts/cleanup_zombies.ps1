# SOTA Zombie Process Cleanup Script
# Target: Port 8001 (Dark App Factory API)

$port = 8001
Write-Host "Searching for zombie processes on port $port..." -ForegroundColor Cyan

$connection = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue

if ($connection) {
    $pids = $connection.OwningProcess | Select-Object -Unique
    foreach ($pid in $pids) {
        try {
            $process = Get-Process -Id $pid -ErrorAction Stop
            Write-Host "Terminating zombie process: $($process.ProcessName) (PID: $pid)" -ForegroundColor Yellow
            Stop-Process -Id $pid -Force
            Write-Host "Successfully terminated PID $pid." -ForegroundColor Green
        }
        catch {
            Write-Host "Failed to terminate PID $pid. It may already be gone or require elevated permissions." -ForegroundColor Red
        }
    }
}
else {
    Write-Host "No active connections found on port $port. Surface is clear." -ForegroundColor Green
}
