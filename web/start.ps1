param(
    [switch]$Automated
)

# Dark App Factory web launcher (FastAPI + static index.html)
$WebPort = 10738
$McpPort = 10739
$ProjectRoot = Split-Path -Parent $PSScriptRoot

function Kill-Port($Port) {
    Write-Host "Checking for port squatters on $Port..." -ForegroundColor Yellow
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        foreach ($c in $connections) {
            $p = Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue
            if ($p) {
                Write-Host "Found squatter $($p.ProcessName) (PID: $($p.Id)) on port $Port. Terminating..." -ForegroundColor Red
                Stop-Process -Id $p.Id -Force -ErrorAction SilentlyContinue
            }
        }
        Start-Sleep -Seconds 1
    }
}

Kill-Port $WebPort
Kill-Port $McpPort

Set-Location $ProjectRoot
$env:PYTHONPATH = "$ProjectRoot;$ProjectRoot\src"
$env:PORT = "$WebPort"

Write-Host "Starting Dark App Factory web server on http://127.0.0.1:$WebPort ..." -ForegroundColor Green

# Start the backend in the background
$proc = Start-Process uv -ArgumentList "run", "--no-project", "--with", "fastapi", "--with", "uvicorn", "--with", "pydantic", "--with", "openai", "--with", "rich", "--with", "python-dotenv", "--with", "tenacity", "python", ".\web\server.py" -NoNewWindow -PassThru

# Basic readiness polling
$retry = 0
$maxRetries = 20
Write-Host "Waiting for backend to be ready..." -ForegroundColor Gray
while ($retry -lt $maxRetries) {
    try {
        $client = New-Object System.Net.WebClient
        $null = $client.DownloadString("http://127.0.0.1:$WebPort/api/status")
        Write-Host "Backend is ready!" -ForegroundColor Green
        break
    } catch {
        $retry++
        Start-Sleep -Seconds 1
    }
}

if (-not $Automated) {
    Write-Host "Launching browser..." -ForegroundColor Cyan
    Start-Process "http://127.0.0.1:$WebPort"
} else {
    Write-Host "Automated mode: skipping browser launch." -ForegroundColor Gray
}

# Keep script alive to monitor the process
Wait-Process -Id $proc.Id -ErrorAction SilentlyContinue

