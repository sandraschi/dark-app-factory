"""MCP client — connect to remote MCP servers via HTTP/SSE, list tools, call tools."""

from __future__ import annotations

import json
import logging
import os
from typing import Any

import httpx

logger = logging.getLogger("dark_factory")

MCP_HEADERS = {
    "Accept": "application/json, text/event-stream",
    "Content-Type": "application/json",
}


class McpClient:
    """Lightweight MCP client for one server over HTTP/SSE."""

    def __init__(self, name: str, url: str):
        self.name = name
        self.url = url.rstrip("/")
        self._http = httpx.AsyncClient(timeout=30.0, headers=MCP_HEADERS)

    async def list_tools(self) -> list[dict[str, Any]]:
        """Call tools/list and return the tool list."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {},
        }
        try:
            resp = await self._http.post(self.url, json=payload)
            resp.raise_for_status()
            result = resp.json()
            return result.get("result", {}).get("tools", [])
        except Exception as e:
            logger.warning("MCP %s tools/list failed: %s", self.name, e)
            return []

    async def call_tool(self, tool_name: str, arguments: dict[str, Any] | None = None) -> dict[str, Any]:
        """Call a tool on the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments or {}},
        }
        try:
            resp = await self._http.post(self.url, json=payload)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            logger.warning("MCP %s tools/call %s failed: %s", self.name, tool_name, e)
            return {"jsonrpc": "2.0", "id": 2, "error": {"code": -1, "message": str(e)}}

    async def close(self):
        await self._http.aclose()


class McpGateway:
    """Manages connections to multiple MCP servers."""

    def __init__(self):
        self._clients: dict[str, McpClient] = {}
        self._tool_index: dict[str, list[dict]] = {}  # server_name -> tools

    def load_from_env(self):
        """Read MCP_SERVERS env var and connect to each."""
        raw = os.environ.get("MCP_SERVERS", "{}")
        try:
            servers = json.loads(raw)
        except json.JSONDecodeError:
            logger.warning("MCP_SERVERS is not valid JSON: %s", raw)
            servers = {}
        for name, url in servers.items():
            self._clients[name] = McpClient(name, url)

    def add_server(self, name: str, url: str):
        self._clients[name] = McpClient(name, url)

    async def refresh_tools(self):
        """Fetch tool lists from all connected servers."""
        for name, client in self._clients.items():
            tools = await client.list_tools()
            if tools:
                self._tool_index[name] = tools

    async def call(self, server: str, tool: str, args: dict | None = None) -> dict:
        client = self._clients.get(server)
        if not client:
            return {"jsonrpc": "2.0", "error": {"code": -1, "message": f"Unknown server: {server}"}}
        return await client.call_tool(tool, args)

    def get_all_tools(self) -> list[dict]:
        result = []
        for server, tools in self._tool_index.items():
            for t in tools:
                entry = dict(t)
                entry["server"] = server
                result.append(entry)
        return result

    def server_status(self) -> dict[str, bool]:
        return {name: name in self._tool_index for name in self._clients}

    async def close_all(self):
        for client in self._clients.values():
            await client.close()
