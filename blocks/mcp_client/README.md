# MCP Client Block

Connect to any MCP server via HTTP/SSE and proxy its tools as REST endpoints for webapp consumption.

**Triggers**: discord, email, mcp, integration, chat, notification, slack, sms

**Env vars**:
| Variable | Default | Description |
|----------|---------|-------------|
| `MCP_SERVERS` | `{"example": "http://localhost:10800/mcp"}` | JSON dict of server name to MCP SSE/HTTP URL |

**API endpoints**: `/api/mcp/tools`, `/api/mcp/{server}/{tool}`

**Dependencies**: `pip: httpx>=0.27.0`
