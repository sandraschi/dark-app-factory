"""CLI: stdio (default) or HTTP streamable MCP."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .server import mcp

logger = logging.getLogger("dark_app_factory_mcp")


def _build_app() -> FastAPI:
    _mcp_http = mcp.http_app()
    app = FastAPI(title="dark-app-factory-mcp", lifespan=_mcp_http.lifespan)
    app.mount("/mcp", _mcp_http)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:10738",
            "http://127.0.0.1:10738",
            "http://localhost:10739",
            "http://127.0.0.1:10739",
            "http://tauri.localhost",
            "https://tauri.localhost",
            "tauri://localhost",
        ],
        allow_origin_regex=r"https?://(?:[a-zA-Z0-9-]+\.ts\.net|.*?\.tail-[a-f0-9]+\.ts\.net|tauri\.localhost|localhost|127\.0\.0\.1|192\.168\.\d{1,3}\.\d{1,3}|10\.\d{1,3}\.\d{1,3}\.\d{1,3}|100\.\d{1,3}\.\d{1,3}\.\d{1,3})(?::\d+)?$|^tauri://localhost$",
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    return app


def main() -> None:
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser(description="Dark App Factory MCP fleet adapter")
    g = parser.add_mutually_exclusive_group()
    g.add_argument("--stdio", action="store_true", help="MCP over stdio (default)")
    g.add_argument("--http", action="store_true", help="MCP streamable HTTP")
    parser.add_argument("--host", default=os.getenv("MCP_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("MCP_PORT", "10739")))
    parser.add_argument("--path", default=os.getenv("MCP_PATH", "/mcp"))
    args = parser.parse_args()
    # Strip --mode flags so downstream parsers don't choke
    sys.argv = [a for a in sys.argv if a not in ("--http", "--stdio")]
    use_http = args.http
    if not args.stdio and not args.http:
        use_http = False
    try:
        if use_http:
            logger.info("MCP HTTP %s:%s%s", args.host, args.port, args.path)
            app = _build_app()
            config = uvicorn.Config(app, host=args.host, port=args.port, log_level="info")
            asyncio.run(uvicorn.Server(config).serve())
        else:
            logger.info("MCP stdio")
            asyncio.run(mcp.run_stdio_async())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
