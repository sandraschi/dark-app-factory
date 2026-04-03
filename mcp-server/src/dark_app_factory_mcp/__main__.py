"""CLI: stdio (default) or HTTP streamable MCP."""

from __future__ import annotations

import argparse
import asyncio
import logging
import os
import sys

from .server import mcp

logger = logging.getLogger("dark_app_factory_mcp")


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
    use_http = args.http
    if not args.stdio and not args.http:
        use_http = False
    try:
        if use_http:
            logger.info("MCP HTTP %s:%s%s", args.host, args.port, args.path)
            asyncio.run(
                mcp.run_http_async(host=args.host, port=args.port, path=args.path)
            )
        else:
            logger.info("MCP stdio")
            asyncio.run(mcp.run_stdio_async())
    except KeyboardInterrupt:
        sys.exit(0)


if __name__ == "__main__":
    main()
