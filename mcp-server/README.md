# Dark App Factory — embedded MCP (fleet adapter)

This package lives under `mcp-server/` inside the main repo (Option B: adapter in-tree).

## What it does

Exposes a small FastMCP surface so agents and fleet tooling can treat Dark App Factory like other MCP nodes: health checks against the web dashboard, launch `web/start.ps1`, tail `logs/factory.log`, read `web/settings.json`.

## Ports

| Surface | Port | Notes |
|--------|------|--------|
| Web dashboard | 10738 | FastAPI + static UI (`web/server.py`) |
| MCP streamable HTTP | 10739 | This adapter (`/mcp` by default) |

## Run (stdio, Claude Desktop)

```powershell
Set-Location D:\Dev\repos\dark-app-factory\mcp-server
uv sync
uv run daf-mcp --stdio
```

## Run (HTTP, fleet / local probes)

```powershell
Set-Location D:\Dev\repos\dark-app-factory\mcp-server
uv run daf-mcp --http --port 10739
```

Environment: `MCP_HOST`, `MCP_PORT`, `MCP_PATH` (default `/mcp`), `DAF_WEB_BASE` (default `http://127.0.0.1:10738`).
