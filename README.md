# Dark App Factory

<p align="center">
  <a href="https://github.com/casey/just"><img src="https://img.shields.io/badge/just-ready_to_go-7c5cfc?style=flat-square&logo=just&logoColor=white" alt="Just"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.13+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python"></a>
  <a href="https://github.com/PrefectHQ/fastmcp"><img src="https://img.shields.io/badge/FastMCP-3.2-7c5cfc?style=flat-square" alt="FastMCP"></a>
</p>

Generate a working web application from a plain-text description. Runs locally on Ollama. No cloud required.

## Quick Start

```powershell
git clone https://github.com/sandraschi/dark-app-factory
cd dark-app-factory
just
```

This opens an interactive dashboard showing all available commands. Run `just bootstrap` to install dependencies, then `just serve` or `just dev` to start.

### Manual Setup

If you don't have `just` installed:

## Configuration

Minimal `.env`:

```env
FOREMAN_MODEL=llama3.1:latest
WORKER_MODEL=qwen2.5-coder:latest
WORKER_BASE_URL=http://localhost:11434/v1
OLLAMA_CONTEXT_LENGTH=65536
```

Full reference: [docs/CONFIGURATION.md](docs/CONFIGURATION.md)

## MCP integration

Dark App Factory exposes itself as an MCP server so it can be used from Claude Desktop or as a RoboFang "AppBuilder" hand.

```json
"mcpServers": {
  "dark-app-factory": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/dark-app-factory", "run", "daf-mcp", "--stdio"]
  }
}
```

Ports: dashboard `10738`, MCP `10739`.

## Documentation

| Doc | Contents |
|-----|----------|
| [docs/INSTALL.md](docs/INSTALL.md) | Prerequisites, setup, model recommendations |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | Pipeline, specialists, DTU, reconciler |
| [docs/USAGE.md](docs/USAGE.md) | Vibe format, CLI reference, common workflows |
| [docs/CONFIGURATION.md](docs/CONFIGURATION.md) | All env vars and `.env` options |
| [docs/SKILLS.md](docs/SKILLS.md) | Domain skill files — what they cover and how to add new ones |
| [reports/deep-assess-2026-07-29.md](reports/deep-assess-2026-07-29.md) | Current deep assessment: open defects and the fix plan |
| [docs/OPENAI_AGENTS_SDK_PROPOSAL.md](docs/OPENAI_AGENTS_SDK_PROPOSAL.md) | v2.0 architecture proposal |
| [docs/STRONGDM_ANALYSIS.md](docs/STRONGDM_ANALYSIS.md) | Comparison with StrongDM Factory |
| [docs/REMOTE_CLIENT_DEMO.md](docs/REMOTE_CLIENT_DEMO.md) | Running at a client site via Tailscale |
| [docs/FULL_AUTO_DEPLOYMENT.md](docs/FULL_AUTO_DEPLOYMENT.md) | Gap analysis: domain, host, HTTPS |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [PRD.md](PRD.md) | Product requirements and roadmap |

## Project status

v0.2.1-beta. The pipeline now includes JS/TS static gates (`tsc --noEmit`, `vite build`, `node --check`), an import-to-dependency closure check that verifies every imported package is declared in `package.json`/`requirements.txt`, and the deep-crawl no longer materialises icon-library components as local files.

Complex apps with many specialists will sometimes need a second pass.
