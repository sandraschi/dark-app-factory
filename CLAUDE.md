# dark-app-factory — Agent Behavioral Instructions

## Stack
- Python 3.11+ with FastAPI backend (web/server.py), FastMCP 3.2+ MCP adapter (mcp-server/)
- Ollama for local LLM orchestration
- Tauri 2.0 native wrapper in native/
- Web dashboard at web/ (CDN TailwindCSS)

## Key Files
| File | Purpose |
|------|---------|
| `factory.py` | Pipeline orchestrator |
| `web/server.py` | FastAPI dashboard backend |
| `mcp-server/src/dark_app_factory_mcp/server.py` | FastMCP tools |
| `run_server.py` | PyInstaller entry point |
| `foreman.py` | Planner (specs + scenarios generation) |
| `worker.py` | Code generation engine |

## Standards
- Ruff for Python linting: `uv run ruff check src/`
- Tests: `uv run pytest tests/ -q`
- Pre-commit hooks installed via `just bootstrap`
- Ports: dashboard 10738, MCP 10739
