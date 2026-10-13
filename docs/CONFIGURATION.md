# Configuration

All configuration is via environment variables. Copy `.env.example` to `.env` — the factory loads it automatically on startup.

## Model configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `FOREMAN_MODEL` | `qwen3.6:27b` | Model used for planning (Foreman). Needs strong instruction-following and long context. Used once per run. |
| `FOREMAN_BASE_URL` | `http://localhost:11434/v1` | OpenAI-compatible base URL for the Foreman model. |
| `FOREMAN_API_KEY` | `ollama` | API key. Set to your real key when using a remote provider. |
| `WORKER_MODEL` | `qwen2.5-coder:32b-instruct-q4_K_M` | Model used for all file generation. Used heavily — pick for speed and code quality. |
| `WORKER_BASE_URL` | `http://localhost:11434/v1` | Base URL for the Worker model. Can differ from Foreman. |
| `WORKER_API_KEY` | `ollama` | API key for the Worker model. |
| `OLLAMA_CONTEXT_LENGTH` | `32768` | Context window size. **Set to `65536` minimum.** The factory generates large prompts. |

### Dual-LLM on one RTX 4090 (Goliath) -- two models resident

The factory has two roles (`src/llm_client.py`): `foreman` (research + blueprint + judge, temp 0.7, called a few times) and `worker` (19 specialists in `worker.py`, `asyncio.gather` per dependency level, called hundreds of times). Both default to `http://localhost:11434/v1` but with different `FOREMAN_MODEL` / `WORKER_MODEL`. On a 24GB 4090 you can keep **two** models resident for true parallel council work.

**Recommended pair (fits 24GB, true parallel):**

```env
# Foreman = quality/planning (14GB)
FOREMAN_MODEL=mistral-small:24b
FOREMAN_BASE_URL=http://localhost:11434/v1
FOREMAN_API_KEY=ollama

# Worker = speed/codegen (7.1GB) -> 14 + 7.1 = 21.1GB + KV headroom, both stay in VRAM
WORKER_MODEL=mistral-nemo:12b
WORKER_BASE_URL=http://localhost:11434/v1
WORKER_API_KEY=ollama

OLLAMA_CONTEXT_LENGTH=32768
```

Set Ollama to keep two models loaded:

```powershell
[System.Environment]::SetEnvironmentVariable("OLLAMA_MAX_LOADED_MODELS","2","User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_NUM_PARALLEL","2","User")
[System.Environment]::SetEnvironmentVariable("OLLAMA_KEEP_ALIVE","10m","User")
# restart Ollama afterwards; verify with: ollama ps
```

VRAM math (Q4_K_M): `muse-glimmer` 18GB + `nemo` 7.1GB = 25GB -> swaps (not parallel). `qwen3.6-35b-a3b` 23GB + anything = no. Budget pair `nemo` 7.1GB + `pdurugyan/qwen3.5-9b` 6.6GB = 13.7GB fits with huge headroom for long KV at 32k.

Alternatives:
- Max quality (swaps, sequential): `FOREMAN_MODEL=muse-glimmer:latest` + `WORKER_MODEL=qwen2.5-coder:32b-instruct-q4_K_M`
- Budget (max parallel, 13GB): `FOREMAN_MODEL=mistral-nemo:12b` + `WORKER_MODEL=pdurugyan/qwen3.5-9b-deepseek-v4-flash-Q4_K_M-v_2:latest`

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
| `APP_PORT_START` | `19300` | Lower bound of the window the Judge allocates generated-app ports from. |
| `APP_PORT_END` | `19400` | Upper bound of that window. |

The generated app's ports are allocated from the `APP_PORT_START` to
`APP_PORT_END` window and exported to the app as `PORT` and `VITE_PORT`. Keep
this window clear of the common dev-server ports (3000, 5173, 8000, 8080). The
Judge only treats a listener on an assigned port as the generated app, so
overlapping the window with your own dev servers reintroduces the risk of
auditing the wrong process.

## Boot and install

| Variable | Default | Description |
|----------|---------|-------------|
| `SKIP_APP_INSTALL` | `false` | Set to `true` to skip installing the generated app's dependencies before the Judge boots it. Only useful when `node_modules` and the Python environment are already prepared. |
| `APP_INSTALL_TIMEOUT` | `600` | Seconds allowed for each install command (node and python are timed separately). |

The installer is chosen automatically: `bun install` if bun is on PATH, else
`pnpm install`, else `npm install --legacy-peer-deps --no-audit --no-fund`.
Python uses `pip install -r requirements.txt`. The node step is skipped when
`node_modules` already exists in the output directory.

Install output and per-process boot logs are written to
`output_XXX/.factory-logs/`.

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
# Dual-LLM on 4090: FOREMAN=mistral-small:24b (14GB), WORKER=mistral-nemo:12b (7.1GB) -> 21GB fits
FOREMAN_MODEL=mistral-small:24b
FOREMAN_BASE_URL=http://localhost:11434/v1
FOREMAN_API_KEY=ollama

WORKER_MODEL=mistral-nemo:12b
WORKER_BASE_URL=http://localhost:11434/v1
WORKER_API_KEY=ollama

OLLAMA_CONTEXT_LENGTH=32768

# ── Ports ─────────────────────────────────────────────────────────────────────
FACTORY_PORT=8001
DASHBOARD_PORT=8002
MCP_PORT=10739
APP_PORT_START=19300
APP_PORT_END=19400

# ── Boot / install ────────────────────────────────────────────────────────────
SKIP_APP_INSTALL=false
APP_INSTALL_TIMEOUT=600

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
