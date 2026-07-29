# Architecture

## Pipeline overview

```
vibe.md
  │
  ▼
┌─────────────────────────────────────────────────────┐
│  FOREMAN  (foreman.py)                              │
│  Reads vibe, produces specs.md + scenarios.md        │
│  LLM: high-capability model, called once per run    │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
┌─────────────────────────────────────────────────────┐
│  WORKER  (worker.py)                                │
│                                                     │
│  Step 1  DTU starts on :8001                        │
│  Step 2  Stack profile detected from specs          │
│  Step 3  File manifest planned (all paths)          │
│  Step 4  Specialist Council runs (parallel tiers)   │
│  Step 5a App.tsx Reconciler (React only)            │
│  Step 5b Deep-crawl (missing import resolution)     │
│  Step 6  manifest.json + landing page generated     │
│  Step 7  Judge: installs deps, boots app on assigned│
│          ports, executes scenarios, verdict         │
│  Step 8  Output directory finalised                 │
└───────────────────────┬─────────────────────────────┘
                        │
                        ▼
                  output_XXX/
```

## Foreman

`foreman.py` takes `vibe.md` and produces two files:

- `specs/specs.md` — technical specification: pages, data model, integrations, stack profile
- `scenarios/scenarios.md` — user scenarios used by the Judge for Playwright test generation

The Foreman also handles `enrich`: given a terse vibe, it expands it into a structured brief before planning.

The stack profile is embedded in `specs.md` as a JSON block. The Worker reads it to select specialist configurations, dependency sets, and folder structures.

## Specialist Council

19 specialists run in dependency-resolved parallel tiers. Each specialist owns a set of file path patterns and is responsible for generating those files.

| Specialist | Owns | Requires |
|------------|------|----------|
| Professor | skill context injection | — |
| Registrar | `package.json`, `requirements.txt`, `Dockerfile`, `.env*`, `vite.config.ts` | — |
| Nervos | WebSocket / messaging layer | — |
| Plumber | `main.py`, `server.js`, `routers/`, `routes/`, `schemas/`, `models/` | Professor |
| Sculptor | `src/App.tsx`, `src/pages/**`, `src/components/**` | Professor |
| Morpheus | `auth/`, security middleware | Plumber |
| Raggy | RAG / vector search modules | Plumber |
| WebFinder | Web scraping, external API clients | Plumber |
| Archivist | ePub/PDF/Mobi parsing | Plumber |
| Maestro | Audio / music modules | Nervos |
| Auditor | Excel/Word, data validation | — |
| Picasso | SVG, illustrations | — |
| Shakespeare | Marketing copy | — |
| Tesla | Robotics, IoT, ROS | Nervos |
| Amodei | AI/LLM integration, Ollama | Plumber, Sculptor |
| Houdini | Animations, Three.js | Sculptor |
| Librarian | `README.md`, docs | Plumber |
| Propagandist | `marketing/` kit | Shakespeare, Librarian |
| Generalist | Everything not claimed | All above |

Tiers are resolved from the `requires` graph. Specialists in the same tier run with `asyncio.gather`. Each specialist validates its own output and retries up to `MAX_RETRIES` times on failure.

## App.tsx Reconciler (v1.8.0)

Specialists run independently and do not know what other specialists will produce. This caused `App.tsx` to reference pages and components that didn't exist, crashing Vite on startup.

The reconciler runs after all specialists complete (step 5a). It:

1. Reads the actual contents of `src/pages/` and `src/components/` on disk
2. Builds an explicit list of what was generated
3. Regenerates `App.tsx` with imports and routes grounded in that list
4. Validates the result (framer-motion named imports, export default, no phantom imports)
5. Retries once if validation fails

This is the safety net for the most common build failure. The Sculptor's initial `App.tsx` generation is also grounded in the planned file list from `shared_context`, so mismatches are caught at two points.

## Deep-crawl (step 5b)

After the reconciler, the deep-crawl scans generated files for import references and JSX element usage that point to files not yet generated. It resolves them by calling the appropriate specialist.

Priority order:
1. Explicit import paths (`from './pages/Foo'` → `src/pages/Foo.tsx`, Sculptor)
2. JSX element names not covered by any explicit import (heuristic: `*Page`, `*View`, `*Screen` → `pages/`, else `components/`)

Maximum depth: `MAX_CRAWL_DEPTH` passes (default 3).

## Skills system

The Professor specialist loads a domain skill file at the start of each build. Skills inject mandatory pages, data models, compliance requirements, and integration patterns into all specialist prompts.

Skill selection: the Professor shows the LLM a compact index (filename + description) and the first 8k chars of specs. The LLM returns a filename. The Professor reads that file and stores its content in `shared_context["SKILL_DATA"]`, where every other specialist can read it.

See [SKILLS.md](SKILLS.md) for the full list and how to add new ones.

## Digital Twin Universe (DTU)

The DTU starts on port `8001` before the build. It provides mock implementations of common external APIs so the Judge can boot and test the generated app without real credentials.

Generated apps are written by Plumber to read all external URLs from environment variables. `run_manifest.py` injects those variables pointing at DTU when running the app during testing.

Available mocks: Stripe, Auth, Email, SMS, Storage, Discord, Slack, Weather, generic Webhook.

Debug endpoints:
```
GET :8001/health
GET :8001/dtu/services     # registered mocks
GET :8001/dtu/log          # request audit log
```

## Judge

The Judge runs after the build completes. It:

1. Allocates two free ports from the app port window (default 19300-19400)
2. Boots the generated app via `run_manifest.py`, which installs dependencies
   first and receives the assigned ports plus the DTU env vars
3. Confirms the app is actually listening on a port the factory assigned
4. Parses `scenarios/scenarios.md` and executes each scenario against the live app
5. Runs Rodney (or Playwright as fallback) for general UI verification
6. Scores the result against `JUDGE_PASS_THRESHOLD`
7. Writes `critique.md` to both the repo root and the output directory on FAIL

The critique is available to the reconciler for a rework loop (v2.0 feature, see [OPENAI_AGENTS_SDK_PROPOSAL.md](OPENAI_AGENTS_SDK_PROPOSAL.md)).

### Boot and verification contract (0.2.1-beta)

Three properties hold, and each of them replaces a defect that made the Judge
unable to evaluate anything reliably.

**Dependencies are installed before boot.** The factory emits source files only.
`RunManifest.boot()` runs the install first: `bun install`, else `pnpm install`,
else `npm install --legacy-peer-deps`, plus `pip install -r requirements.txt`
when a `requirements.txt` is present. The node step is skipped when
`node_modules` already exists. Without this every boot failed with
"Cannot find module" and the Judge scored a dead server.

**Ports are assigned, not discovered.** The Judge allocates ports and exports
them to the child as `PORT` / `VITE_PORT`. Startup detection polls only those
ports. The previous implementation probed a shared list of common dev ports
(3000, 8000, 5173, 5174, 8080) and treated any listener as the generated app,
which on a developer machine could point the audit at an unrelated server and
report a pass for a build that never started. The default window sits outside
the common dev range for exactly this reason.

**A dead app cannot pass.** If nothing ever listened on an assigned port, the
Judge returns FAIL deterministically with the install errors, per-process exit
codes and boot log tails attached. The LLM verdict is demoted to advisory in
that case. This is the anti-gaslighting backstop for the whole pipeline.

Supporting details:

- Child stdout and stderr go to `output_XXX/.factory-logs/<component>.log`.
  They were previously written to unread pipes, which deadlocks a verbose
  process such as Vite once the OS pipe buffer fills.
- `terminate()` kills the whole process tree. `Popen.terminate()` on a
  `shell=True` process only kills the shell, leaving the real server alive and
  holding its port, which then fed the next run a false successful boot.
- `RunManifest.boot()` returns a `boot_report` dict (install result, assigned
  ports, process exit codes, log excerpts) that is injected into the Judge
  prompt as mechanical evidence alongside the scenario results.
- `kill_zombies()` covers the ports the system actually binds
  (3000, 5173, 5174, 8000, 8001, 8002, 8080, 10738, 10739) in addition to the
  app port window.

Port and process helpers live in `src/utils/ports.py`, shared by `factory.py`,
`judge.py` and `run_manifest.py`.

### Known gap

There is still no check that the packages a generated file imports appear in
`package.json` or `requirements.txt`. Installing dependencies fixes the boot
mechanism, but an app whose `server.js` requires `express` while `package.json`
never declares it will still fail to start. Static checking for JS and TS is
also absent: Ruffy covers ruff and mypy, which are Python only. Both are
tracked in `reports/deep-assess-2026-07-29.md` as the Day 2 work.

## Dashboard

`start_factory.ps1` starts both the web dashboard (`8002`) and the DTU (`8001`). The dashboard polls `/api/progress` for build status and `/api/deliberations` (SSE) for real-time specialist events.

## MCP server

`mcp-server/` is a thin FastMCP adapter that exposes the factory to Claude Desktop and RoboFang. Tools: `factory_run`, `factory_status`, `factory_outputs`, `factory_assess`, `factory_fleet`, `factory_stop`, `factory_launch`.

Port `10739` (streamable HTTP) or `--stdio` for Claude Desktop.

## Output structure

```
output_XXX/
  main.py / server.js           # Backend entry point
  requirements.txt              # Python deps
  package.json                  # Node deps (or frontend-only)
  vite.config.ts
  Dockerfile
  .env.example
  src/
    App.tsx                     # Router shell (reconciled)
    pages/                      # Page components
    components/                 # Shared components
    hooks/                      # Custom React hooks
    store/                      # State management
  routers/                      # FastAPI routers (Python)
  schemas/                      # Pydantic schemas (Python)
  models/                       # DB models
  routes/                       # Express routes (Node)
  auth/                         # Auth middleware
  README.md                     # Auto-generated docs for this app
  www/index.html                # Landing page
  marketing/                    # Press release, blog, social kit
  skills/                       # Skill summary used for this build
  manifest.json                 # Entry points, consumed by run_manifest.py
  critique.md                   # Judge verdict, written on FAIL
  .factory-logs/                # Install and per-process boot logs
  demos/                        # Showboat audit artifact, screenshots
```

## Model economics

The Foreman is called once per run. All file generation goes through the Worker. For a typical 40-file React + FastAPI build, the Worker handles roughly 50–70 LLM calls. Using a local 14B coder model keeps this fast and free. The Foreman benefits from a stronger model but the cost per run is small even with a remote API.

Recommended setup:
- Foreman: `llama3.1:70b` (local) or `claude-sonnet-4-6` (remote, ~$0.05/plan)
- Worker: `qwen2.5-coder:14b` Q4 at ~40 tok/s on a 24GB GPU

## v2.0 direction

The current orchestration loop is hand-rolled. The [OpenAI Agents SDK proposal](OPENAI_AGENTS_SDK_PROPOSAL.md) covers migrating to a declarative agent framework with native MCP fleet attachment and a Judge-triggered rework loop. This is the path to the "multi-agent recursive self-healing" goal in the PRD.
