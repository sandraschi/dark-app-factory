# Dark App Factory web launcher (FastAPI + static index.html)
$WebPort = 10738
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Get-PidsOnPort([int]$Port) {
    $matches = netstat -ano -p tcp | Select-String -Pattern "LISTENING\s+(\d+)$" | Select-Object -ExpandProperty Line
    $pids = @()
    foreach ($line in $matches) {
        if ($line -match "^\s*TCP\s+\S+:$Port\s+\S+\s+LISTENING\s+(\d+)\s*$") {
            $procId = [int]$Matches[1]
            if ($procId -gt 4) { $pids += $procId }
        }
    }
    return $pids | Select-Object -Unique
}

Write-Host "Checking for port squatters on $WebPort..." -ForegroundColor Yellow
foreach ($p in (Get-PidsOnPort -Port $WebPort)) {
    Write-Host "Found squatter (PID: $p). Terminating..." -ForegroundColor Red
    try { Stop-Process -Id $p -Force -ErrorAction Stop } catch { Write-Host "Warning: Could not terminate PID $p." -ForegroundColor Gray }
}

Set-Location $ProjectRoot
$env:PYTHONPATH = "$ProjectRoot;$ProjectRoot\src"
$env:PORT = "$WebPort"

Write-Host "Starting Dark App Factory web server on http://127.0.0.1:$WebPort ..." -ForegroundColor Green
# Project packaging is currently not hatch-configured for editable install; use uv no-project runtime deps.
uv run --no-project `
    --with fastapi `
    --with uvicorn `
    --with pydantic `
    --with openai `
    --with rich `
    --with tenacity `
    --with python-dotenv `
    python ".\web\server.py"

