# Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` — the factory loads it automatically on startup.

## Model configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FOREMAN_MODEL` | `llama3.1:latest` | Model used for planning (Foreman). Needs strong instruction-following and long context. Used once per run. |
| `FOREMAN_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL for the Foreman model. |
| `FOREMAN_API_KEY` | `ollama` | API key. Set to your real key when using a remote provider. |
| `WORKER_MODEL` | `qwen2.5-coder:latest` | Model used for all file generation. Used heavily — pick for speed and code quality. |
| `WORKER_BASE_URL` | `http://localhost:11434/v1` | Base URL for the Worker model. Can differ from Foreman. |
| `WORKER_API_KEY` | `ollama` | API key for the Worker model. |
| `OLLAMA_CONTEXT_LENGTH` | `32768` | Context window size. **Set to `65536` minimum.** The factory generates large prompts. |

### Using a remote model for the Foreman

The Foreman is called once per run, so a remote API is cheap here and often produces better plans:

```env
FOREMAN_MODEL=claude-sonnet-4-6
FOREMAN_BASE_URL=https://api.anthropic.com/v1
FOREMAN_API_KEY=sk-ant-...

WORKER_MODEL=qwen2.5-coder:14b
WORKER_BASE_URL=http://localhost:11434/v1
```

Or OpenAI:

```env
FOREMAN_MODEL=gpt-4o
FOREMAN_BASE_URL=https://api.openai.com/v1
FOREMAN_API_KEY=sk-...
```

## Port configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FACTORY_PORT` | `8001` | DTU mock server port. |
| `DASHBOARD_PORT` | `8002` | Web dashboard port. |
| `MCP_PORT` | `10739` | MCP server port (streamable HTTP). |

## Generation settings

| Variable | Default | Description |
|----------|---------|-------------|
| `MAX_RETRIES` | `3` | Per-specialist retry limit on validation failure. |
| `MAX_CRAWL_DEPTH` | `3` | Deep-crawl passes to resolve missing imports. |
| `JUDGE_PASS_THRESHOLD` | `0.7` | Judge pass rate (0.0–1.0) required to mark a build successful. |
| `PLAYWRIGHT_HEADLESS` | `true` | Run Playwright in headless mode. Set to `false` to watch the browser. |

## Output

| Variable | Default | Description |
|----------|---------|-------------|
| `OUTPUT_DIR` | `output_001` | Base name for generated output directories. Auto-incremented. |
| `SPECS_DIR` | `specs` | Where `specs.md` and `scenarios.md` are written. |

## Logging

| Variable | Default | Description |
|----------|---------|-------------|
| `LOG_LEVEL` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR`. |
| `LOG_FILE` | `logs/factory.log` | Log file path. |

## DTU (mock services)

The DTU injects these variables into generated apps at test time. You do not need to set them — they are set automatically. They are listed here for reference and for cases where you want to point at real services.

| Variable | DTU default | Real service example |
|----------|-------------|----------------------|
| `STRIPE_API_URL` | `http://localhost:8001/stripe` | `https://api.stripe.com` |
| `AUTH_API_URL` | `http://localhost:8001/auth` | Your auth service |
| `EMAIL_API_URL` | `http://localhost:8001/email` | `https://api.sendgrid.com` |
| `SMS_API_URL` | `http://localhost:8001/sms` | `https://api.twilio.com` |
| `STORAGE_API_URL` | `http://localhost:8001/storage` | S3 endpoint |
| `DISCORD_WEBHOOK_URL` | `http://localhost:8001/discord/webhooks/x/x` | Real Discord webhook |
| `SLACK_WEBHOOK_URL` | `http://localhost:8001/slack/hooks/x` | Real Slack webhook |
| `WEATHER_API_URL` | `http://localhost:8001/weather` | OpenWeatherMap |
| `WEBHOOK_URL` | `http://localhost:8001/webhook` | Your webhook target |

## Full `.env.example`

```env
# ── Models ────────────────────────────────────────────────────────────────────
FOREMAN_MODEL=llama3.1:latest
FOREMAN_BASE_URL=http://localhost:11434/v1
FOREMAN_API_KEY=ollama

WORKER_MODEL=qwen2.5-coder:14b
WORKER_BASE_URL=http://localhost:11434/v1
WORKER_API_KEY=ollama

OLLAMA_CONTEXT_LENGTH=65536

# ── Ports ─────────────────────────────────────────────────────────────────────
FACTORY_PORT=8001
DASHBOARD_PORT=8002
MCP_PORT=10739

# ── Generation ────────────────────────────────────────────────────────────────
MAX_RETRIES=3
MAX_CRAWL_DEPTH=3
JUDGE_PASS_THRESHOLD=0.7
PLAYWRIGHT_HEADLESS=true

# ── Output ────────────────────────────────────────────────────────────────────
OUTPUT_DIR=output_001
SPECS_DIR=specs
LOG_LEVEL=INFO
LOG_FILE=logs/factory.log
```
