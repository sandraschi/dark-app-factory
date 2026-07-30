# Blocks System — Plan (updated)

**Goal**: Turn DAF from "LLM writes every line from scratch" to "LLM assembles and configures pre-built modules."

## Priority Order

1. **MCP Client block** — generated app connects to any fleet MCP server (Discord, email, Plex, etc.). Highest leverage: 187 pre-built integrations for free.
2. **Stripe block** — payment processing, subscriptions, webhooks.
3. **Auth block** — JWT auth, registration, login, OAuth stubs.

---

## Block: MCP Client

### Why

The fleet has 187 MCP servers. Each one is a proven, working integration. If a generated app can connect to these via MCP client, it instantly inherits all that capability without the LLM generating a single line of integration code.

The generated app becomes a thin UI shell over MCP tools.

### Architecture

```
Generated App
  ├── FastAPI backend
  │     └── /api/mcp/{server}/{tool}  ──HTTP/SSE──►  discord-mcp
  │                                                   email-mcp
  │                                                   calibre-mcp
  │                                                   ...
  └── React frontend
        └── McpPanel (browse tools, invoke, see results)
```

### How it works

1. User sets `MCP_SERVERS={"discord": "http://localhost:10757/mcp", "email": "http://localhost:10813/mcp"}` in `.env`
2. Backend MCP client connects to each server at startup
3. Block exposes `GET /api/mcp/tools` — aggregated tool list from all servers
4. Block exposes `POST /api/mcp/{server}/{tool}` — invoke a tool on a server
5. Frontend gets a generic `McpPanel` component — dropdown of servers → tools → input args → results
6. The LLM specialist writes the specific pages that call specific tools (e.g. a Discord channel browser)

### block.json

```json
{
  "name": "mcp-client",
  "version": "0.1.0",
  "description": "Connect to any fleet MCP server — Discord, email, Plex, Calibre, etc.",
  "triggers": ["discord", "email", "mcp", "integration", "chat", "notifications"],
  "dependencies": {
    "python": ["mcp>=1.0.0", "httpx>=0.27.0"]
  },
  "env_vars": {
    "MCP_SERVERS": "{\"discord\": \"http://localhost:10757/mcp\", \"email\": \"http://localhost:10813/mcp\"}"
  },
  "specialists": {
    "Plumber": { "append": ["backend/routes.py"] },
    "Sculptor": { "append": ["frontend/components/McpPanel.tsx"] }
  },
  "backend_routes": ["/api/mcp/tools", "/api/mcp/{server}/{tool}"],
  "frontend_pages": []
}
```

### Files

| File | Purpose |
|------|---------|
| `blocks/mcp-client/backend/client.py` | MCP client — connect, list tools, call tool |
| `blocks/mcp-client/backend/routes.py` | FastAPI router: `GET /api/mcp/tools`, `POST /api/mcp/{server}/{tool}` |
| `blocks/mcp-client/frontend/McpPanel.tsx` | Generic tool browser — select server → tool → fill args → see result |
| `blocks/mcp-client/frontend/McpStatus.tsx` | Connection status indicator per server |
| `blocks/mcp-client/glue/main.py.append` | `app.include_router(mcp_router)` |
| `blocks/mcp-client/tests/test_client.py` | Tests with mocked MCP server |

---

## Block: Stripe

### block.json triggers
`["payment", "stripe", "checkout", "subscription", "billing"]`

### Files
| File | Purpose |
|------|---------|
| `blocks/stripe/backend/routes.py` | Checkout, webhook, subscriptions |
| `blocks/stripe/backend/models.py` | Product, Price, Subscription |
| `blocks/stripe/backend/service.py` | Stripe API wrapper |
| `blocks/stripe/frontend/pages/PricingPage.tsx` | Pricing table |
| `blocks/stripe/frontend/components/CheckoutButton.tsx` | Stripe checkout button |
| `blocks/stripe/glue/main.py.append` | Route registration |
| `blocks/stripe/glue/App.tsx.append` | Page route |

---

## Block: Auth

### block.json triggers
`["auth", "login", "register", "user", "oauth", "jwt", "password"]`

---

## Block Directory Structure

```
blocks/
  mcp-client/
    block.json
    README.md
    backend/
      client.py       # MCP connection manager
      routes.py       # REST proxy endpoints
    frontend/
      McpPanel.tsx
      McpStatus.tsx
    glue/
      main.py.append
    tests/
      test_client.py
  stripe/
    ...
  auth/
    ...
```

## Implementation Phases

## Shipped Blocks

| Block | Status | Description |
|-------|--------|-------------|
| MCP Client | **Shipped** | Connect to any fleet MCP server — proxy tools via REST |
| Stripe | **Shipped** | Checkout, subscriptions, webhooks, pricing UI |
| Webshop | **Shipped** | Products, cart, orders, inventory, Stripe checkout |
| Membership | **Shipped** | JWT auth, member/customer/employee DB, roles, registration UI |

## Next Blocks (planned)

| Block | Priority | Description |
|-------|----------|-------------|
| Email | High | SendGrid/SMTP, templates, verification flows |
| Storage | High | File upload, S3, image resizing |
| Admin Panel | High | Auto-generated CRUD, charts, user management |
| Calendar/Booking | Medium | Availability, appointments, sync |
| Blog/CMS | Medium | Markdown editor, articles, RSS |
| AI Chat | Medium | Chat UI with Ollama integration |
| Notifications | Low | Push/email/SMS routing, templates |

## Implementation Phases

| Phase | Tasks | Status |
|-------|-------|--------|
| **P1: Infrastructure** | `blocks/` dir, `block.json` schema + loader, `Registrar.match_blocks()`, `Registrar.install_block()`, tests | **Done** |
| **P2: MCP Client** | `blocks/mcp_client/` — backend client, routes, frontend panel, glue, tests | **Done** |
| **P3: Stripe** | `blocks/stripe/` — backend, frontend, glue, tests | **Done** |
| **P4: Webshop** | `blocks/webshop/` — products, cart, orders, inventory | **Done** |
| **P5: Membership** | `blocks/membership/` — auth, member/customer/employee DB, roles | **Done** |
| **P6: Generalize** | Block registry, Settings UI, versioning | Pending |
