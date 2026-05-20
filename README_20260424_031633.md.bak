# Dark App Factory

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff) [![Built with Just](https://img.shields.io/badge/Built_with-Just-000000?style=flat-square&logo=gnu-bash&logoColor=white)](https://github.com/casey/just)

**"Software Factories for the Rest of Us."**

A local-first, low-cost implementation of the "Software Factory" methodology (Spec -> Scenarios -> Agent Loop).
Inspired by [StrongDM Factory](https://factory.strongdm.ai) (they target $1k/dev/day; we do it for free).
Designed for local-first development teams using Ollama, DeepSeek, and compatible local models.

## Architecture v1.7

The workflow uses an async-parallel orchestrator, a set of 19 specialists, and a web dashboard for real-time monitoring.
For a deep dive, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

- **Foreman**: Planning stage that generates specs, scenarios, and enriched prompt text.
- **Specialists**: 18 domain specialists plus a generalist running in dependency-resolved parallel tiers.
- **Multi-Stack**: Python (FastAPI/Flask/Django) or Node.js (Express) backends. React, HTMX, or API-only frontends.
- **Marketing Generator**: Produces a marketing kit (press release, blog, social media, Reddit, Discord, Product Hunt, landing page).
- **Judge**: Playwright-based UI/API auditing.
- **DTU-Lite**: Digital Twin Universe for local mocks (Stripe, Auth, etc.).

## Fleet MCP (embedded, Option B)

The repo includes a small FastMCP adapter under `mcp-server/` so Dark App Factory can appear in the fleet like other MCP nodes without moving code to a separate repository.

| Surface | Port | Start |
|--------|------|--------|
| Web dashboard | 10738 | `.\web\start.ps1` |
| MCP (streamable HTTP) | 10739 | `.\mcp-server\start.ps1` |

From `mcp-server/`: `uv sync` then `uv run daf-mcp --stdio` (Claude Desktop) or `uv run daf-mcp --http --port 10739`. Tool: `factory_fleet` (health, launch dashboard, tail logs, read settings file).

## Quick Start

### Prerequisites

- Python 3.12+
- Ollama running locally (`ollama serve`)
- **MANDATORY**: Set context window to 64k+ tokens:
  ```
  set OLLAMA_CONTEXT_LENGTH=65536
  ```

### 1. Define your Vibe

Edit `vibe.md` with your idea. Specify the stack:
```markdown
## Tech Stack
- **Backend**: python/fastapi
- **Frontend**: react
- **Database**: postgresql
```

Valid options:
- **Backend**: `python/fastapi`, `python/flask`, `python/django`, `node/express`
- **Frontend**: `react`, `htmx`, `none`
- **Database**: `postgresql`, `mysql`, `sqlite`, `mongodb`

### 2. Enrich the Vibe (Optional but Recommended)

```
python foreman.py enrich --vibe vibe.md
```

LLM expands your terse vibe into a rich brief with domain-specific features, integrations, and branding suggestions. Review `enriched_vibe.md`, edit as needed.

### 3. Run the Foreman

```
python foreman.py plan --vibe enriched_vibe.md
```

Generates `specs/specs.md` and `scenarios/scenarios.md` with embedded stack profile.

### 4. Run the Factory (Full Pipeline)

**Option A: CLI**
```
python factory.py run
```

**Option B: Dashboard (Recommended)**
```powershell
.\start_factory.ps1
```
Launches the dashboard on `http://localhost:8002` with real-time progress tracking.

This runs the complete pipeline:
1. Domain Research (Oracle)
2. Foreman Planning
3. Worker Building (parallel specialists)
4. Landing Page Generation
5. DTU Mock Environment
6. Judge verification
7. Auto-launch + Audit

Or run the worker directly:
```
python worker.py build --specs specs/specs.md --output output_001
```

### 5. Help & Logs

```
python foreman.py help --level advanced --topic dtu
python foreman.py log --tail 50
python foreman.py log --export
```

## Specialists (19)

| Specialist | Domain | Temperature | Requires |
|---|---|---|---|
| Professor | Skill battery | 0.2 | - |
| Plumber | Backend (Python/Node) | 0.15 | Professor |
| Sculptor | Frontend (React/HTMX) | 0.4 | Professor |
| Registrar | Infrastructure (deps, Docker) | 0.1 | - |
| Nervos | Heartbeat, messaging, plugins | 0.2 | - |
| Raggy | RAG, vector search | 0.2 | - |
| WebFinder | Web scraping, APIs | 0.2 | - |
| Archivist | ePub/PDF/Mobi parsing | 0.2 | - |
| Maestro | Audio, music | 0.3 | - |
| Auditor | Excel/Word, data validation | 0.2 | - |
| Picasso | SVG, illustrations | 0.5 | - |
| Shakespeare | Marketing copy, content | 0.7 | - |
| Librarian | Documentation, README | 0.6 | Plumber |
| Morpheus | Security, auth, encryption | 0.1 | Plumber |
| Tesla | Robotics, IOT, ROS | 0.15 | Nervos |
| Amodei | AI/LLM integration, Ollama | 0.3 | Plumber, Sculptor |
| Houdini | Animations, Three.js | 0.45 | Sculptor |
| Propagandist | Marketing distribution | 0.65 | Shakespeare, Librarian |
| Generalist | Catch-all | 0.3 | All above |

## Configuration

Configure models via environment variables or `.env`:

```
# Foreman (The Brains) -- expensive, used sparingly
FOREMAN_MODEL=llama3.1:latest
FOREMAN_BASE_URL=http://localhost:11434/v1

# Workers (The Labor) -- cheap, used extensively
WORKER_MODEL=qwen2.5-coder:latest
WORKER_BASE_URL=http://localhost:11434/v1

# MANDATORY: Context window
OLLAMA_CONTEXT_LENGTH=65536
```

## Generated Output

Each factory run produces:

```
output_XXX/
  main.py / server.js     # Backend entry point
  requirements.txt / package.json  # Dependencies
  src/                     # Frontend components (if applicable)
  routers/ schemas/ ...    # Backend modules (Python)
  routes/ models/ ...      # Backend modules (Node)
  README.md                # Auto-generated documentation
  marketing/               # Press release, blog, social, emails, Reddit, Discord, PH
  www/                     # Landing page (index.html)
  Dockerfile               # Production container
```

## Digital Twin Universe (DTU)

The DTU is a local mock server that replaces external APIs during testing. It allows the Judge to boot and test generated apps without real API keys, credentials, or network calls.

### How It Works

1.  **Generated code** reads all external API URLs from environment variables (e.g., `STRIPE_API_URL`, `AUTH_API_URL`). The Plumber specialist enforces this pattern.
2.  **DTU starts** on port 8001 before the build step.
3.  **RunManifest** injects env vars pointing to DTU when booting the generated app:
    ```
    STRIPE_API_URL=http://localhost:8001/stripe
    AUTH_API_URL=http://localhost:8001/auth
    EMAIL_API_URL=http://localhost:8001/email
    ...
    ```
4.  **All external API calls** are intercepted by DTU mocks (always succeed).
5.  **Judge** tests the app with Playwright while DTU handles backend dependencies.

### Available Mock Services

| Service | Endpoint | Env Var |
|---|---|---|
| Stripe | `/stripe/v1/payment_intents`, `/stripe/v1/charges`, `/stripe/v1/balance` | `STRIPE_API_URL` |
| Auth | `/auth/login`, `/auth/register`, `/auth/verify`, `/auth/me` | `AUTH_API_URL` |
| Email | `/email/send` | `EMAIL_API_URL` |
| SMS | `/sms/send` | `SMS_API_URL` |
| Storage | `/storage/upload`, `/storage/files/{key}` | `STORAGE_API_URL` |
| Discord | `/discord/webhooks/{id}/{token}` | `DISCORD_WEBHOOK_URL` |
| Slack | `/slack/hooks/{id}` | `SLACK_WEBHOOK_URL` |
| Weather | `/weather/current`, `/weather/forecast` | `WEATHER_API_URL` |
| Webhook | `/webhook/{path}` (generic) | `WEBHOOK_URL` |

### Debugging

- Service registry: `GET http://localhost:8001/dtu/services`
- Request log: `GET http://localhost:8001/dtu/log?limit=50`
- Health check: `GET http://localhost:8001/health`

For the full technical explanation of the Digital Twin pattern, see [ARCHITECTURE.md](docs/ARCHITECTURE.md).

## Dashboard

The factory features a real-time web UI on port 8002.
- **Progress Tracking**: 0-100% build indicator with granular status logs.
- **Specialist Council**: Live monitoring of each specialist's execution status and file generation.
- **Build Queue**: Queue and relaunch vibes directly from the browser.

## Startup Protocol

To ensure zero-friction development, the factory implements a robust startup logic:
1. **Zombie Cleanup**: Proactively scans and terminates processes blocking ports 8001 (DTU) and 8002 (Web).
2. **Environment Synchronization**: Aligns all singleton instances (Logger, ProgressTracker) before execution.
3. **Launch Wrapper**: Use `.\start_factory.ps1` for a safe, one-command deployment.

## Documentation

- [ARCHITECTURE.md](docs/ARCHITECTURE.md) -- System design (includes DTU, Progress Tracking, Pyramid Summaries)
- [ASSESSMENT.md](ASSESSMENT.md) -- Technical assessment
- [STRONGDM_ANALYSIS.md](docs/STRONGDM_ANALYSIS.md) -- StrongDM Factory comparison, methodology, economics
- [REMOTE_CLIENT_DEMO.md](docs/REMOTE_CLIENT_DEMO.md) -- Practical use at client site (notebook + Tailscale + goliath)
- [FULL_AUTO_DEPLOYMENT.md](docs/FULL_AUTO_DEPLOYMENT.md) -- Gap analysis: domain, host, HTTPS, deploy (not yet implemented)
- [MONETIZATION_PLAN.md](docs/MONETIZATION_PLAN.md) -- 100/300 products, Austrian setup, landing page
- [CHANGELOG.md](CHANGELOG.md) -- Version history
- [PRD.md](PRD.md) -- Product requirements
- [META_MCP_INTEGRATION.md](docs/META_MCP_INTEGRATION.md) -- meta-mcp cross-utilization


##  Installation

### Prerequisites
- [uv](https://docs.astral.sh/uv/) installed (RECOMMENDED)
- Python 3.12+

###  Quick Start
Run immediately via `uvx`:
```bash
uvx foreman
```

###  Claude Desktop Integration
Add to your `claude_desktop_config.json`:
```json
"mcpServers": {
  "foreman": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/dark-app-factory", "run", "foreman"]
  }
}
```


## 🛡️ Industrial Quality Stack

This project adheres to **SOTA 14.1** industrial standards for high-fidelity agentic orchestration:

- **Python (Core)**: [Ruff](https://astral.sh/ruff) for linting and formatting. Zero-tolerance for `print` statements in core handlers (`T201`).
- **Webapp (UI)**: [Biome](https://biomejs.dev/) for sub-millisecond linting. Strict `noConsoleLog` enforcement.
- **Protocol Compliance**: Hardened `stdout/stderr` isolation to ensure crash-resistant JSON-RPC communication.
- **Automation**: [Justfile](./justfile) recipes for all fleet operations (`just lint`, `just fix`, `just dev`).
- **Security**: Automated audits via `bandit` and `safety`.
