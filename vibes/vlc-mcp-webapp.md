# VLC Control: MCP Server + Webapp

> Build an MCP server and webapp for controlling VLC media player on Windows. Package for PyPI and GitHub.

## Requirements

1. **MCP Server** (FastMCP, stdio):
   - Tools: `vlc_play`, `vlc_pause`, `vlc_stop`, `vlc_volume`, `vlc_status`, `vlc_open_file`
   - Invoke VLC via subprocess or `--rc-host` telnet control
   - Configurable VLC path (default: detect from PATH or `C:\Program Files\VideoLAN\VLC\vlc.exe`)

2. **Webapp** (FastAPI + React or HTMX):
   - Dashboard with play/pause/stop, volume slider, file picker
   - Status panel (current file, time, state)
   - Same backend logic as MCP tools (shared service layer)

3. **Packaging**:
   - pyproject.toml with entry point `vlc-mcp`
   - GitHub Actions for test and release
   - PyPI publishable

## Tech Stack

- **Backend**: python/fastapi
- **Frontend**: react
- **Database**: sqlite (optional, for playback history)

## Constraints

- Windows-only (VLC path, subprocess)
- No placeholders; all tools must invoke real VLC or return clear error if VLC not found
