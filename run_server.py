"""PyInstaller entrypoint for dark-app-factory HTTP sidecar."""

from __future__ import annotations

import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    base = Path(sys._MEIPASS)
else:
    base = Path(__file__).resolve().parent / "mcp-server"
if str(base / "src") not in sys.path:
    sys.path.insert(0, str(base / "src"))

os.environ.setdefault("MCP_TRANSPORT", "http")

if __name__ == "__main__":
    from fastapi import FastAPI
    from dark_app_factory_mcp.server import mcp as _mcp

    _mcp_http = _mcp.http_app()
    app = FastAPI(title="dark-app-factory", lifespan=_mcp_http.lifespan)
    app.mount("/mcp", _mcp_http)

    host = os.environ.get("DAF_HOST", "127.0.0.1")
    port = int(os.environ.get("DAF_PORT", os.environ.get("MCP_PORT", "10738")))
    log_level = os.environ.get("DAF_LOG_LEVEL", "info")
    uvicorn.run(app, host=host, port=port, log_level=log_level)
