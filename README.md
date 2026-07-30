# Dark App Factory

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
</p>

Generate a web application scaffold from a plain-text description. Runs locally on Ollama. No cloud required.

> **Status: v0.2.2-beta — proof of concept.** Produces a structured project scaffold you can edit. Not a production app generator. See limitations below.

## Quick Start

```bash
git clone https://github.com/sandraschi/dark-app-factory
cd dark-app-factory
just bootstrap
just serve   # backend on :10738
just dev     # frontend on :10740
```

Requires Python 3.13+, [uv](https://docs.astral.sh/uv/), [just](https://github.com/casey/just), and Ollama running with a coder model.

## How it works

```
vibe.md → [Foreman (LLM)] → specs.md + scenarios.md
              ↓
[Worker: 19 specialist agents in parallel tiers]
    Plumber, Sculptor, Registrar, Morpheus, Nervos, Raggy,
    WebFinder, Archivist, Maestro, Auditor, Picasso,
    Shakespeare, Librarian, Propagandist, Houdini,
    Tesla, Amodei, Generalist, Hawks
              ↓
[Judge: install deps → boot app → run scenarios → verdict]
              ↓
output_XXX/   ← generated app scaffold (backend + frontend + landing page + marketing)
```

Each specialist owns file patterns matching its domain (e.g. Plumber generates `main.py`/`server.js` and API routes, Sculptor generates React components, Morpheus handles auth). Specialists run in dependency-resolved parallel tiers — Plumber produces routes before Sculptor imports them.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for details.

## What's good

- **Methodology works**: The foreman → parallel specialists → empirical judge loop is the right shape for AI-generated code. The tiered, dependency-resolved council with upstream context injection produces coherent multi-file projects, not isolated stubs.
- **Honest failure mode**: The Judge installs dependencies, assigns ports deterministically, and fails hard when the app doesn't boot. No false PASS from probing the wrong port.
- **Real file output**: Every run produces a complete project directory with backend, frontend, landing page, test scenarios, deploy scripts, and marketing copy.
- **Digital Twin Universe**: Built-in mock server for Stripe, Auth, Email, SMS, Storage — the generated app's boot is tested against these mocks, not real APIs.
- **SOTA web dashboard**: 9-page React app with real-time build progress, LLM provider auto-detection, specialist status grid, and generated file tree.
- **135 fast tests**: Ruff check + format clean, pre-commit hooks, GitHub CI configured.

## What's not good (honest)

| Issue | Root cause | Impact |
|-------|------------|--------|
| **Output quality depends heavily on model** | 8B models produce thin, sometimes broken code. 27B-32B models do better but run at 2-5 tok/s on consumer GPUs. | A generated app almost always needs manual fixing before it runs correctly. |
| **No import-to-dependency repair** | The closure check detects missing npm/pip packages in the lint report, but doesn't auto-install or regenerate. | First boot fails if the LLM skipped a dependency. The error message tells you what's missing, but you fix it manually. |
| **No JS/TS repair loop** | `tsc --noEmit` and `vite build` run as gates, but failures are reported, not fixed. | TypeScript errors in generated code require manual correction. |
| **Slow with local models** | Full pipeline takes 5-30 minutes depending on model size. | Iteration is painful. Not suitable for rapid prototyping. |
| **Single-user, in-memory state** | Build runs tracked in process memory. No persistence, no multi-user. | Restarting the server loses run history. |
| **Windows-tested only** | The zombie hunter, port scanner, and process-tree kill use Windows APIs. | Linux/macOS support exists in the port module but hasn't been tested. |

## Building Blocks (shipped)

The LLM doesn't write these from scratch — it installs, configures, and glues them. Each is triggered by keywords in the vibe description.

| Block | Triggers | What it provides |
|-------|----------|-----------------|
| **MCP Client** | `discord`, `email`, `mcp`, `integration`, `chat`, `notification` | Connect generated apps to any fleet MCP server. `GET /api/mcp/tools` lists all tools from all servers, `POST /api/mcp/{server}/{tool}` proxies calls. Frontend panel for interactive tool browsing. |
| **Stripe** | `payment`, `stripe`, `checkout`, `subscription`, `billing`, `pricing` | Checkout sessions, subscriptions, webhooks, customer portal. React pricing table with Stripe Checkout redirect. Env: `STRIPE_SECRET_KEY`, `STRIPE_PUBLISHABLE_KEY`. |
| **Webshop** | `shop`, `store`, `ecommerce`, `cart`, `inventory`, `catalog`, `product` | Product catalog with category filtering, shopping cart, stock management, order processing with Stripe integration fallback. Full React shop UI. |
| **Membership** | `member`, `register`, `login`, `auth`, `user`, `club`, `org`, `employee`, `customer`, `team` | JWT auth, member/employee/customer database with roles (admin, member, employee, customer), registration, login, directory search. React login page and member directory. Env: `JWT_SECRET`. |

A vibe like _"Build a webshop for a climbing club with member registration, product catalog, and Stripe checkout"_ triggers all 4 blocks. The LLM writes ~50 lines of glue; the blocks provide ~1500 lines of tested implementation.

## Roadmap: towards production

### Next blocks (suggested)

| Block | Purpose | Why |
|-------|---------|-----|
| **Email** | Transactional email via SendGrid/SMTP with templates, verification flows | Every app needs email. Currently each specialist generates a fragile `smtplib` call. |
| **Storage** | File upload with S3/local FS abstraction, image resizing, progress | Plumber currently generates `open()` calls that break in production. |
| **Admin Panel** | Auto-generated CRUD tables, charts, user management UI | Sculptor spends 40% of tokens on admin pages that all look the same. |
| **Calendar/Booking** | Availability slots, appointment booking, calendar sync | Half the generated apps are booking systems (dentist, salon, consult). |
| **Blog/CMS** | Markdown editor, article management, RSS, SEO meta | Second most common request after booking. |
| **AI Chat** | Pre-built chat UI with Ollama/LM Studio integration | Every generated app wants an AI assistant nowadays. |
| **Notifications** | Push, email, SMS notification routing with template system | Currently each specialist invents its own notification system. |

### Medium term (v0.4)

- **Convergence loop**: judge FAIL → extract compiler errors → feed back to worker → re-generate affected files → re-judge.
- **Output persistence** — SQLite-based run history and assessment storage.
- **Multi-model routing** — fast model (3B) for simple specialists, expensive model (27B+) for complex ones.
- **Cross-platform** — Linux/macOS CI testing and port scanner fixes.

### Longer term

- **Block marketplace**: share and version blocks as `npm`/`pip` packages.
- **Plugin architecture**: third-party specialists and blocks via a registry.

## Configuration

Minimal `.env` (copy from `.env.example`):

```env
FOREMAN_MODEL=qwen3.6:27b
WORKER_MODEL=qwen2.5-coder:32b-instruct-q4_K_M
WORKER_BASE_URL=http://localhost:11434/v1
OLLAMA_CONTEXT_LENGTH=65536
```

Full reference: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

## MCP integration

Use from Claude Desktop, Cursor, or any MCP client:

```json
"mcpServers": {
  "dark-app-factory": {
    "command": "uv",
    "args": ["run", "--directory", "/path/to/dark-app-factory", "daf-mcp", "--stdio"]
  }
}
```

Ports: dashboard `10738`, MCP `10739`.

## Documentation

- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) — Pipeline, specialist council, DTU, reconciler
- [docs/CONFIGURATION.md](docs/CONFIGURATION.md) — All env vars
- [docs/USAGE.md](docs/USAGE.md) — Vibe format, CLI reference, common workflows
- [CHANGELOG.md](CHANGELOG.md) — Version history
- [docs/BLOCKS_PLAN.md](docs/BLOCKS_PLAN.md) — Building blocks system plan
- [PRD.md](PRD.md) — Product requirements and roadmap

## License

MIT
