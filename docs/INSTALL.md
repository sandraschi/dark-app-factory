# Installation

## Requirements

| Requirement | Minimum | Notes |
|-------------|---------|-------|
| Python | 3.12+ | 3.13 works fine |
| uv | latest | `pip install uv` or `winget install astral-sh.uv` |
| Ollama | latest | [ollama.com](https://ollama.com) |
| Node.js | 20+ | Only needed to run generated Node.js apps |
| Playwright | latest | Installed via `uv sync`, browsers via `playwright install` |
| RAM | 16 GB | 32 GB recommended for large Ollama models |
| GPU VRAM | 8 GB | 16–24 GB for 27B+ models at full quality |

## Setup

```powershell
# Clone
git clone https://github.com/sandraschi/dark-app-factory.git
cd dark-app-factory

# Install Python dependencies
uv sync

# Install Playwright browsers
uv run playwright install chromium
```

## Ollama models

The factory uses two model roles. You can point both at the same model if you want simplicity.

**Foreman** — used once per run for planning. Needs strong instruction-following and long context.
Good choices: `llama3.1:70b`, `qwen2.5:32b`, `deepseek-r1:32b`, or a remote model via API.

**Worker** — used for every file generation call. Needs strong coding output and speed.
Good choices: `qwen2.5-coder:14b`, `qwen2.5-coder:32b`, `deepseek-coder-v2:16b`.

Pull the models you want:

```powershell
ollama pull qwen2.5-coder:14b
ollama pull llama3.1:latest
```

**Context window** — must be set before running Ollama. The factory generates large prompts:

```powershell
$env:OLLAMA_CONTEXT_LENGTH = "65536"
ollama serve
```

Or set it permanently in your system environment variables.

## Environment

Copy `.env.example` to `.env` and edit:

```powershell
Copy-Item .env.example .env
notepad .env
```

Minimum required:

```env
WORKER_MODEL=qwen2.5-coder:14b
FOREMAN_MODEL=llama3.1:latest
OLLAMA_CONTEXT_LENGTH=65536
```

See [CONFIGURATION.md](CONFIGURATION.md) for all options including remote API keys.

## Verify

```powershell
# Check Ollama is reachable
curl http://localhost:11434/api/tags

# Smoke test the factory
python foreman.py help
```

## Claude Desktop (MCP)

Add to `C:\Users\<you>\AppData\Roaming\Claude\claude_desktop_config.json`:

```json
"mcpServers": {
  "dark-app-factory": {
    "command": "uv",
    "args": ["--directory", "D:/Dev/repos/dark-app-factory", "run", "daf-mcp", "--stdio"]
  }
}
```

Restart Claude Desktop. The `factory_run`, `factory_status`, `factory_outputs`, `factory_assess`, and `factory_fleet` tools will appear.

## Updating

```powershell
git pull
uv sync
```
