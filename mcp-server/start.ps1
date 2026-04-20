Param([switch]$Headless)

# --- SOTA Headless Standard ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }
# ------------------------------

# Dark App Factory â€” embedded MCP HTTP (fleet / local)
$ErrorActionPreference = "Stop"
$McpPort = 10739
$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $PSScriptRoot

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) {
    Write-Host "uv not found. Install Astral uv, then re-run." -ForegroundColor Red
    exit 1
}

$env:MCP_TRANSPORT = "http"
$env:MCP_HOST = "127.0.0.1"
$env:MCP_PORT = "$McpPort"
$env:MCP_PATH = "/mcp"

Write-Host "Starting dark-app-factory MCP on http://127.0.0.1:${McpPort}/mcp ..." -ForegroundColor Green
uv sync
uv run daf-mcp --http --host 127.0.0.1 --port $McpPort --path /mcp

