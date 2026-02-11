# Dark App Factory: Practical Use at Client Site

**Scenario**: Demo or build at a customer location using a portable notebook, with LLM inference running on a remote server (goliath) over Tailscale.

**Last Updated**: 2026-02-09

---

## Architecture

```
Client Site (Notebook)                    Home/Office (Goliath Server)
---------------------                    -----------------------------
- Dark App Factory (orchestrator)   -->   Ollama (port 11434)
- Dashboard (port 8002)                    RTX 4090, 24GB VRAM
- DTU (port 8001)                         qwen2.5-coder, deepseek-coder, etc.
- Generated app (varies)
           |
           v
     Tailscale VPN (encrypted, low-latency)
```

The notebook does **not** run any LLM. It sends all inference requests to goliath over Tailscale. The notebook acts as a thin client: orchestration, HTTP calls, dashboard, DTU, and running the generated app.

---

## Notebook Requirements

| Spec | Minimum | Notes |
|------|---------|-------|
| RAM | 16 GB | Plenty for factory + dashboard + DTU + generated app |
| GPU | None | Inference is remote |
| Storage | 2 GB free | Repo, deps, output dirs |
| Python | 3.12+ | Factory runtime |
| Network | Tailscale | Must reach goliath |

---

## Goliath Server Setup

### 1. Ollama Listen on All Interfaces

By default Ollama binds to `127.0.0.1` only. For remote access:

**Windows (PowerShell)**:
```powershell
$env:OLLAMA_HOST = "0.0.0.0"
ollama serve
```

**Linux/macOS**:
```bash
OLLAMA_HOST=0.0.0.0 ollama serve
```

Or set `OLLAMA_HOST=0.0.0.0` in system environment variables before starting Ollama.

### 2. Context Window

Ensure 64k context for code generation:
```powershell
$env:OLLAMA_CONTEXT_LENGTH = "65536"
```

### 3. Firewall

Allow inbound TCP 11434 from Tailscale network (or from the notebook's Tailscale IP).

### 4. Tailscale

Install Tailscale on goliath. Note the Tailscale IP: `tailscale ip -4`

### 5. Required Models

Pull before the demo:
```bash
ollama pull qwen2.5-coder:latest
ollama pull llama3.1:latest
```

---

## Notebook Setup (At Client)

### 1. Prerequisites

- Python 3.12+
- Tailscale installed and logged in
- Git (to clone repo)

### 2. Clone and Install

```powershell
git clone https://github.com/sandraschi/dark-app-factory.git
cd dark-app-factory
pip install -r requirements.txt
```

### 3. Environment Variables

Replace `GOLIATH_TAILSCALE_IP` with goliath's Tailscale IP (e.g. `100.64.1.5`):

```powershell
$env:WORKER_BASE_URL = "http://GOLIATH_TAILSCALE_IP:11434/v1"
$env:FOREMAN_BASE_URL = "http://GOLIATH_TAILSCALE_IP:11434/v1"
$env:WORKER_MODEL = "qwen2.5-coder:latest"
$env:FOREMAN_MODEL = "llama3.1:latest"
$env:OLLAMA_CONTEXT_LENGTH = "65536"
```

### 4. Verify Connection

```powershell
curl http://GOLIATH_TAILSCALE_IP:11434/api/tags
```

Should return JSON with available models.

---

## Demo Workflow

### Before the Meeting

1. Start goliath's Ollama with `OLLAMA_HOST=0.0.0.0`
2. On notebook: connect Tailscale, verify `curl` to goliath works
3. Prepare `vibe.md` in advance or draft with the client live

### During the Demo

1. **Optional**: Start dashboard for visual feedback:
   ```powershell
   python web/server.py
   ```
   Open `http://localhost:8002` in browser.

2. **Enrich** (optional): Expand the vibe with LLM
   ```powershell
   python foreman.py enrich --vibe vibe.md
   ```

3. **Plan**: Generate specs and scenarios
   ```powershell
   python foreman.py plan
   ```

4. **Build**: Run the full factory
   ```powershell
   python factory.py run
   ```

5. **Show**: Factory outputs to `outputs/output_001/`. Run the generated app, show the landing page, walk through the code.

### Latency Expectations

- Each specialist call: 5–60 seconds (depends on model, context, goliath load)
- Full build: 10–30 minutes for a typical app (dentist, beekeeper, etc.)
- Tailscale adds ~10–50 ms per request. Acceptable.

---

## Building for the Client

### Same Setup

Use the same notebook + Tailscale + goliath configuration. The client's vibe defines the app; everything else is identical.

### Output Delivery

- **Option A**: Copy `outputs/output_XXX/` to USB or cloud. Client runs it on their machine.
- **Option B**: Run the generated app on the notebook during the session, show it live. Leave the output folder with the client.
- **Option C**: Copy output to goliath, run there, expose via Tailscale or ngrok for client to access.

### Client's Machine

The generated app needs Python 3.12+ (for FastAPI) or Node 18+ (for React). If the client has neither, deliver a Dockerized build (Registrar generates Dockerfile) or a static export.

---

## Troubleshooting

| Issue | Check |
|-------|-------|
| `Connection refused` to goliath | Ollama on goliath has `OLLAMA_HOST=0.0.0.0`? Firewall allows 11434? |
| Tailscale not connected | Both machines on same Tailscale network? `tailscale status` |
| Timeout on LLM calls | Large context (64k) can take 60s+. Increase HTTP timeout in llm_client if needed. |
| Generated app won't start | `pip install -r requirements.txt` or `npm install` in output dir. Check `main.py` vs `app.py` entry. |
| Dashboard shows no progress | ProgressTracker may not sync if subprocess. Check dashboard logs. |

---

## Offline / No Tailscale Fallback

If the client site has no network and you cannot use Tailscale:

1. **Run Ollama locally on the notebook**:
   - Use a small model (7B) in CPU mode
   - Expect 8–10 GB RAM for the model alone
   - 16 GB RAM may be borderline; smaller models (3B) or quantized variants help
   - Generation will be slow (minutes per file)

2. **Pre-build**:
   - Run the full factory at home/office before the meeting
   - Bring the output on USB, demo the result only

3. **Spec-only demo**:
   - Run only `foreman plan` at home (with goliath)
   - Bring `specs.md` and `scenarios.md` to the client
   - Show the plan, explain the methodology; build later remotely

---

## Checklist

**Before leaving for client**:
- [ ] Goliath Ollama running with `OLLAMA_HOST=0.0.0.0`
- [ ] Models pulled (qwen2.5-coder, llama3.1)
- [ ] Tailscale on both machines
- [ ] Notebook repo cloned, deps installed
- [ ] Env vars set (or in `.env`)

**At client**:
- [ ] Tailscale connected
- [ ] `curl http://GOLIATH_IP:11434/api/tags` works
- [ ] `vibe.md` ready (or drafted with client)
