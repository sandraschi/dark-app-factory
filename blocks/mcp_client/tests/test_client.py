"""Tests for MCP client block."""

from __future__ import annotations

import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest


def _mock_response(status: int, json_data: dict) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.json.return_value = json_data
    resp.raise_for_status = MagicMock()
    return resp


@pytest.fixture
def sample_tools_response():
    return {
        "jsonrpc": "2.0",
        "id": 1,
        "result": {
            "tools": [
                {"name": "send_message", "description": "Send a message to a channel", "inputSchema": {"type": "object"}},
                {"name": "list_channels", "description": "List available channels", "inputSchema": {"type": "object"}},
            ]
        },
    }


@pytest.fixture
def sample_call_response():
    return {"jsonrpc": "2.0", "id": 2, "result": {"content": [{"type": "text", "text": "Message sent"}]}}


@pytest.mark.asyncio
async def test_mcp_client_list_tools(sample_tools_response):
    from blocks.mcp_client.backend.client import McpClient

    client = McpClient("test", "http://localhost:9999/mcp")
    mock_resp = _mock_response(200, sample_tools_response)
    client._http.post = AsyncMock(return_value=mock_resp)

    tools = await client.list_tools()
    assert len(tools) == 2
    assert tools[0]["name"] == "send_message"

    await client.close()


@pytest.mark.asyncio
async def test_mcp_client_call_tool(sample_call_response):
    from blocks.mcp_client.backend.client import McpClient

    client = McpClient("test", "http://localhost:9999/mcp")
    mock_resp = _mock_response(200, sample_call_response)
    client._http.post = AsyncMock(return_value=mock_resp)

    result = await client.call_tool("send_message", {"channel": "general", "text": "hello"})
    assert result["result"]["content"][0]["text"] == "Message sent"

    await client.close()


@pytest.mark.asyncio
async def test_mcp_gateway():
    from blocks.mcp_client.backend.client import McpGateway

    gw = McpGateway()
    gw.add_server("test", "http://localhost:9999/mcp")
    assert "test" in gw._clients
    assert gw.get_all_tools() == []
    assert gw.server_status() == {"test": False}
    await gw.close_all()


@pytest.mark.asyncio
async def test_mcp_gateway_load_from_env():
    from blocks.mcp_client.backend.client import McpGateway

    with patch.dict("os.environ", {"MCP_SERVERS": json.dumps({"discord": "http://localhost:10757/mcp"})}):
        gw = McpGateway()
        gw.load_from_env()
        assert "discord" in gw._clients
        await gw.close_all()


@pytest.mark.asyncio
async def test_mcp_gateway_call_unknown_server():
    from blocks.mcp_client.backend.client import McpGateway

    gw = McpGateway()
    result = await gw.call("nonexistent", "some_tool")
    assert "error" in result
    assert "Unknown server" in result["error"]["message"]
    await gw.close_all()
