# dark-app-factory -- Agent Behavioral Instructions

## Stack
- Python 3.11+ with FastAPI backend (web/server.py), FastMCP 3.2+ MCP adapter (mcp-server/)
- Ollama for local LLM orchestration
- Tauri 2.0 native wrapper in native/
- Web dashboard: web_sota/ (React + Vite + Tailwind + Zustand). web/ is the older CDN-Tailwind dashboard.

## Key Files
| File | Purpose |
|------|---------|
| `factory.py` | Pipeline orchestrator (zombie hunt, DTU lifecycle, phase sequencing) |
| `foreman.py` | Planner (specs + scenarios generation) |
| `worker.py` | Code generation engine (Specialist Council, App.tsx reconciler, deep-crawl) |
| `judge.py` | Quality gate (port allocation, scenario execution, verdict) |
| `run_manifest.py` | Boot orchestrator for generated apps (install, ports, process lifecycle) |
| `src/utils/ports.py` | Port allocation and process-tree kill, shared by the three above |
| `src/specialists/council.py` | The 19 specialists |
| `web/server.py` | FastAPI dashboard backend |
| `mcp-server/src/dark_app_factory_mcp/server.py` | FastMCP tools |
| `run_server.py` | PyInstaller entry point |

## Standards
- Ruff for Python linting: `uv run ruff check src/`
- Tests: `uv run pytest tests/ -q`
  - Note: `tests/test_e2e_scaffold.py` currently hangs. Use
    `uv run pytest tests -q --ignore=tests/test_e2e_scaffold.py` for a fast run (about 7s).
- Pre-commit hooks installed via `just bootstrap`
- Ports: dashboard 10738, MCP 10739, DTU 8001. Generated apps get ports from the
  `APP_PORT_START`-`APP_PORT_END` window (default 19300-19400).

## Invariants worth protecting

These exist because each one was a real defect. Do not undo them.

1. **Never boot a generated app without installing its dependencies first.** The factory
   emits source only. `RunManifest.boot()` installs before starting anything.
2. **Never detect the generated app by probing a shared list of common dev ports.** Ports
   are allocated by the caller, exported as `PORT` / `VITE_PORT`, and only those are polled.
   Probing 3000/5173/8000 can latch onto an unrelated server and pass a build that never ran.
3. **Never use `Popen.terminate()` on a `shell=True` process.** It kills the shell and
   leaves the real server holding its port. Use `kill_pid_tree()` from `src/utils/ports.py`.
4. **Never pipe a long-lived child's stdout/stderr without draining it.** Write to a log
   file. An unread pipe buffer deadlocks Vite.
5. **A dead app cannot pass the Judge.** The deterministic FAIL gate in `run_judgement()` is
   the anti-gaslighting backstop. Do not let an LLM verdict override it.

## Current state

v0.2.1-beta. See `reports/deep-assess-2026-07-29.md` for the open defect list. The two
largest open items: no cross-check that imported packages appear in `package.json` /
`requirements.txt`, and no JS/TS static gate (Ruffy is ruff + mypy, Python only).
