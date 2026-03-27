# Skill: MCP + Webapp Wrapper for Windows Apps

## 1. Architecture

- **Shared service layer**: Backend logic that invokes the Windows executable (subprocess, CLI).
- **MCP server** (`mcp_server.py`): FastMCP with tools that call the service layer. Stdio transport.
- **Webapp API**: FastAPI routes (`/api/{app}/control`, `/api/{app}/status`) that call the same service layer.
- **Frontend**: React or HTMX dashboard with buttons/sliders that POST to the API.

## 2. File Layout

```
main.py              # FastAPI app (API + optional static serve)
mcp_server.py        # FastMCP entry point, imports service, registers tools
src/
  services/
    vlc_service.py   # or sevenzip_service.py - subprocess invocation
  api/
    routes.py        # /api/vlc/control, /api/vlc/status
pyproject.toml       # [project.scripts] vlc-mcp = "mcp_server:main"
```

## 3. Subprocess Pattern (Windows)

```python
import subprocess
import shutil

def find_vlc() -> str | None:
    paths = [
        r"C:\Program Files\VideoLAN\VLC\vlc.exe",
        shutil.which("vlc"),
    ]
    for p in paths:
        if p and Path(p).exists():
            return p
    return None

def run_vlc(args: list[str], timeout: int = 10) -> subprocess.CompletedProcess:
    exe = find_vlc()
    if not exe:
        raise FileNotFoundError("VLC not found. Install from https://www.videolan.org/")
    return subprocess.run([exe] + args, capture_output=True, text=True, timeout=timeout)
```

## 4. FastMCP Tool Pattern

```python
from fastmcp import FastMCP

mcp = FastMCP("vlc-control")

@mcp.tool()
def vlc_play(file_path: str | None = None) -> dict:
    """Play a media file or resume playback."""
    # Call service layer, return {"status": "ok", "message": "..."}
```

## 5. Packaging (PyPI)

- `pyproject.toml`: `[project.scripts]` entry point for MCP CLI.
- `README.md`: Install with `pip install vlc-mcp`, configure Cursor/Claude to use `vlc-mcp` or `python -m mcp_server`.
- GitHub Actions: `pytest`, `ruff`, build and publish to PyPI.

## 6. VLC-Specific

- Control: `--rc-host=127.0.0.1:4212` for telnet, or CLI `vlc.exe file.mp4 --play-and-exit`.
- Status: Parse telnet response or use `--no-video` for headless.

## 7. 7-Zip-Specific

- Extract: `7z x archive.zip -ooutput_dir -y`
- Compress: `7z a archive.7z folder/`
- List: `7z l archive.zip`
- Test: `7z t archive.zip`
