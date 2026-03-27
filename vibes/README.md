# Sample Vibe Depot

Pre-built vibes for the Dark App Factory. Copy one to `vibe.md` and run the factory.

## Available Vibes

| Vibe | Description |
|------|-------------|
| `vlc-mcp-webapp.md` | MCP server + webapp for controlling VLC media player |
| `7zip-mcp-webapp.md` | MCP server + webapp for 7-Zip archive operations |

## Usage

```powershell
Copy-Item vibes\vlc-mcp-webapp.md vibe.md
python -m factory run
```

Or specify path: `python -m factory run --vibe vibes/vlc-mcp-webapp.md` (if supported).

## Pattern: MCP + Webapp for Windows App Control

These vibes produce:
- **MCP server**: FastMCP with tools callable from Cursor/Claude
- **Webapp**: Dashboard with controls, status, API routes
- **Packaging**: pyproject.toml, GitHub Actions, PyPI-ready

The factory uses the `mcp-windows-app-wrapper` skill when specs mention MCP, Windows app control, VLC, or 7-Zip.
