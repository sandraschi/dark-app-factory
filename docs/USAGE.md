# Usage

## The vibe file

Everything starts with `vibe.md`. It can be as short as a paragraph or as detailed as you like. The Foreman's enrichment step will expand a terse description into a full brief — it's usually worth running.

Minimum viable vibe:

```markdown
# My App

A booking system for a physiotherapy practice in Vienna.
Patients can book appointments online. Staff manage the calendar via a back-office.

## Tech Stack
- Backend: python/fastapi
- Frontend: react
- Database: postgresql
```

Valid stack options:

| Field | Options |
|-------|---------|
| Backend | `python/fastapi`, `python/flask`, `python/django`, `node/express` |
| Frontend | `react`, `htmx`, `none` |
| Database | `postgresql`, `mysql`, `sqlite`, `mongodb` |

The more context you give — specific pages, data fields, integrations needed — the better the output. Vague vibes produce generic apps.

## Step-by-step workflow

### 1. Enrich (optional but recommended)

Expands your terse vibe into a structured brief with suggested pages, features, and integrations:

```powershell
python foreman.py enrich --vibe vibe.md
```

Review and edit `enriched_vibe.md`, then use it as input for the plan step.

### 2. Plan

Generates `specs/specs.md` and `scenarios/scenarios.md`:

```powershell
python foreman.py plan --vibe enriched_vibe.md
```

Read `specs/specs.md` before building. If the Foreman misunderstood something, edit the spec directly — it's faster than re-running.

### 3. Build

**Option A — Dashboard (recommended)**

```powershell
.\start_factory.ps1
```

Opens `http://localhost:8002`. Shows real-time specialist progress, file generation log, and Judge results.

**Option B — CLI**

```powershell
python factory.py run
```

**Option C — Worker only** (skip Foreman, use an existing spec)

```powershell
python worker.py build --specs specs/specs.md --output output_001
```

### 4. Inspect output

```
output_XXX/
  main.py / server.js       # Entry point
  requirements.txt          # or package.json
  src/                      # React components (pages/, components/, hooks/, store/)
  routers/ schemas/         # Python backend modules
  Dockerfile
  README.md                 # Auto-generated docs for the generated app
  www/index.html            # Landing page
  marketing/                # Press release, blog post, social kit
```

### 5. Run the generated app

The Judge does this automatically, but you can also run it manually:

```powershell
python run_manifest.py --output output_XXX
```

This boots the app with DTU environment variables injected so all external API calls (Stripe, email, etc.) hit local mocks instead of real services.

## CLI reference

### foreman.py

```
python foreman.py enrich --vibe vibe.md              # Expand vibe into structured brief
python foreman.py plan --vibe vibe.md                # Generate specs and scenarios
python foreman.py help --level basic                 # Built-in help system
python foreman.py help --level advanced --topic dtu  # Topic-specific help
python foreman.py log --tail 50                      # Tail recent log entries
python foreman.py log --export                       # Export full log
```

### factory.py

```
python factory.py run                                # Full pipeline from specs/specs.md
python factory.py run --output output_custom         # Custom output directory name
python factory.py status                             # Last run status
```

### worker.py

```
python worker.py build --specs specs/specs.md --output output_001
python worker.py build --specs specs/specs.md --output output_001 --dry-run  # List files only
```

## Re-runs and iteration

Output directories are numbered (`output_001`, `output_002`, ...). Each run creates a new one. To iterate on an existing run:

1. Edit `specs/specs.md` directly to fix the problem
2. Run `python worker.py build --specs specs/specs.md --output output_002`

Or delete the output directory and re-run the full pipeline.

## Dashboard

The dashboard at `http://localhost:8002` shows:

- **Progress bar** — 0–100% build milestone indicator
- **Specialist panel** — per-specialist status (queued / running / done / failed)
- **File log** — every file generated, in real time
- **Judge report** — Playwright audit results with per-check pass/fail
- **Build queue** — queue additional vibes without restarting

## DTU (Digital Twin Universe)

The factory starts a local mock server on port 8001 before building. Generated apps are written to read all external API URLs from environment variables (`STRIPE_API_URL`, `AUTH_API_URL`, etc.). When the Judge boots the app, those variables point to DTU, so the app works without any real API keys.

DTU endpoints for debugging:

```
GET http://localhost:8001/health
GET http://localhost:8001/dtu/services    # registered mock services
GET http://localhost:8001/dtu/log         # request audit log
```

Available mocks: Stripe, Auth, Email, SMS, Storage, Discord, Slack, Weather, generic Webhook.

## Logs

```powershell
python foreman.py log --tail 100          # recent entries
python foreman.py log --export            # full export to file
```

Or check `logs/factory.log` directly.

## Common problems

**Vite crashes on startup with import errors**
The App.tsx reconciler (v1.8.0+) should prevent this. If it still happens, check `src/App.tsx` and compare its imports against the actual files in `src/pages/` and `src/components/`. Delete any imports that don't exist and re-run just the Judge: `python factory.py judge --output output_XXX`.

**App boots but pages are blank**
Usually a missing route or a component returning null. Check the browser console. Often fixable by editing the relevant file directly and re-running the Judge.

**Ollama times out mid-build**
Context window too small or model too large for available VRAM. Try a smaller model for workers, or increase `OLLAMA_CONTEXT_LENGTH`.

**Judge reports all checks failed**
The app didn't boot. Check `logs/factory.log` for the Python/Node startup error. Usually a missing dependency or a DB connection string pointing at a non-existent host.
