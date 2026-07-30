"""FastAPI router — proxy REST calls to MCP servers."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from .client import McpGateway

router = APIRouter(prefix="/api/mcp", tags=["mcp"])
gateway = McpGateway()


@router.on_event("startup")
async def _startup():
    gateway.load_from_env()
    await gateway.refresh_tools()


@router.on_event("shutdown")
async def _shutdown():
    await gateway.close_all()


@router.get("/tools")
async def list_mcp_tools():
    """List all tools from all connected MCP servers."""
    tools = gateway.get_all_tools()
    return {"success": True, "servers": gateway.server_status(), "tools": tools, "count": len(tools)}


@router.post("/{server}/{tool:path}")
async def call_mcp_tool(server: str, tool: str, body: dict | None = None):
    """Call a tool on a specific MCP server."""
    result = await gateway.call(server, tool, body or {})
    if "error" in result:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"success": True, "server": server, "tool": tool, "result": result.get("result", {})}
