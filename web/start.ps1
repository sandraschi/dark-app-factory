# Dark App Factory Web Dashboard (reservoir port 10738 per WEBAPP_PORTS.md)
$WebPort = 10738
$ProjectRoot = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)

try {
    $conn = Get-NetTCPConnection -LocalPort $WebPort -ErrorAction SilentlyContinue
    if ($conn) {
        $conn.OwningProcess | Select-Object -Unique | ForEach-Object {
            if ($_ -gt 0) { Stop-Process -Id $_ -Force -ErrorAction SilentlyContinue }
        }
        Start-Sleep -Seconds 1
    }
} catch { }

$env:PYTHONPATH = $ProjectRoot
$env:PORT = $WebPort
Set-Location $ProjectRoot
Write-Host "Starting Dark App Factory Dashboard on port $WebPort..." -ForegroundColor Green
Write-Host "Dashboard: http://localhost:$WebPort" -ForegroundColor Cyan
python web/server.py
