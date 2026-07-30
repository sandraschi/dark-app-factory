# dark-app-factory-mcp

Fleet MCP adapter for Dark App Factory — control generation runs from any MCP client.

## Tools

| Tool | Description |
|------|-------------|
| `factory_fleet(operation)` | ping, web_health, web_status, dashboard_url, launch_dashboard, tail_log, read_settings |
| `factory_run(vibe)` | Start a generation run, returns `run_id` |
| `factory_status(run_id)` | Poll run status, log tail |
| `factory_stop(run_id)` | Cancel running build |
| `factory_launch(output_dir)` | Launch generated app in new console |
| `factory_assess(output_dir)` | Static analysis, Prefab UI card, score 0-100 |
| `factory_outputs(limit)` | List completed output directories |

## Run (stdio, Claude Desktop)

```powershell
cd path/to/dark-app-factory/mcp-server
uv sync
uv run daf-mcp --stdio
```

## Run (HTTP, fleet / local probes)

```powershell
cd path/to/dark-app-factory/mcp-server
uv run daf-mcp --http --port 10739
```

Environment: `MCP_HOST`, `MCP_PORT`, `MCP_PATH` (default `/mcp`), `DAF_WEB_BASE` (default `http://127.0.0.1:10738`).

## Claude Desktop config

```json
"mcpServers": {
  "dark-app-factory": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/dark-app-factory/mcp-server", "daf-mcp", "--stdio"]
  }
}
```
