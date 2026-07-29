
## [0.2.1-beta] - 2026-07-29

### Fixed (Critical: boot and verify path)
- **Generated apps were never given their dependencies before the Judge booted them.**
  `RunManifest.boot()` ran `node server.js` / `python main.py` / `npm run dev` in a fresh
  output directory with no `node_modules` and no installed pip packages, so the boot always
  failed and every scenario ran against a dead server. `RunManifest` now installs first
  (bun, then pnpm, then npm with `--legacy-peer-deps`; `pip install -r requirements.txt` for
  Python), skips when `node_modules` already exists, and records the result.
- **Startup detection could latch onto an unrelated server.** The old `_wait_for_startup()`
  probed a shared list of common dev ports (3000, 8000, 5173, 5174, 8080) and treated any
  listener as the generated app. On a machine running other dev servers this pointed
  Playwright at the wrong application and could produce a PASS for a build that never
  started. Ports are now allocated up front, passed to the child as `PORT` / `VITE_PORT`,
  and only those ports are polled.
- **Orphaned child processes.** `terminate()` called `Popen.terminate()` on a `shell=True`
  process, killing the shell and leaving the real server alive holding its port. Replaced
  with a process-tree kill (`taskkill /F /T` on Windows, process-group kill elsewhere).
- **Zombie hunter scanned the wrong ports.** `kill_zombies()` covered only 19300-19400,
  a range nothing in the system binds. It now also covers the ports actually used
  (3000, 5173, 5174, 8000, 8001, 8002, 8080, 10738, 10739).
- **Child output deadlock.** Components were started with unread `stdout=PIPE, stderr=PIPE`.
  A verbose Vite or npm process fills the OS pipe buffer and blocks forever. Output now goes
  to `.factory-logs/<component>.log` inside the output directory.
- **DTU process leak.** `spin_up_dtu()` returned None while the uvicorn process was still
  alive whenever the health check returned a non-200 status. The orphan then held port 8001
  and blocked every subsequent run. The handle is now returned whenever the process is up.
- **Judge could pass a dead app.** Added a deterministic FAIL gate: if the app never listened
  on its assigned port, the verdict is FAIL with the install errors, process exit codes and
  boot log tails attached, and the LLM commentary is demoted to advisory.

### Added
- `src/utils/ports.py`: shared port allocation, listener detection, and process-tree kill.
  Replaces three divergent copies of this logic in factory.py, judge.py and run_manifest.py.
- `RunManifest.boot_report`: mechanical record of install success, assigned ports, per-process
  exit codes and log excerpts. Injected into the Judge prompt as objective evidence.
- `tests/test_boot_path.py`: 11 tests covering port injection, boot-report defaults and the
  install phase.

### Changed
- `critique.md` is now written both to the repo root (for the next Foreman run) and into the
  output directory, so runs stop overwriting each other's critique.
- `judge._detect_app_port()` is deprecated; it reads the assigned port from the boot report
  rather than probing.
- ruffy_runner.py: added JS/TS static gates (tsc --noEmit, vite build, node --check) and
  import-to-dependency closure check.
- worker.py deep-crawl: bare package import identifiers no longer materialised as local files.
- README.md, llms-full.txt: updated known-gaps list.

### Known issue
- `tests/test_e2e_scaffold.py` hangs (does not complete in 4 minutes). The remaining 135
  tests run in about 7 seconds. Needs a timeout and a marker for the LLM-dependent cases.

## [0.2.0-beta] — 2026-07-29

### Added
- SOTA React+Vite+Tailwind webapp (web_sota/) — 8 pages: Dashboard, Chat, Tools, Skills, Settings, Help, Logs, Inbox
- Chat page with 4 personalities, localStorage persistence, TTS SpeakButton, 6 example prompts
- LLM provider auto-detection (Ollama/LM Studio) in Settings with model selector
- Session context injection: CLAUDE.md, .cursorrules, .claude-plugin/, .windsurfrules, copilot-instructions.md
- Zustand stores for LLM state and backend health
- `just dev`, `just build-web`, `just gates-green` recipes
- CORSMiddleware on both web and MCP HTTP endpoints (fleet standard origins + regex)

### Fixed
- CRITICAL: .env was bundled in NSIS installer instead of .env.example — now fixed
- MCP server uses uvicorn.Server instead of run_http_async() (preserves CORS middleware)
- Hatchling build: added packages directive to pyproject.toml
- 16 pre-existing test failures (ScenarioResult missing scenario_type, parse_http_action keyword priority)

# Changelog

All notable changes to the Dark App Factory will be documented in this file.

## [1.8.0] - 2026-04-24

### Fixed (Critical)
- **App.tsx Vite startup crash**: The #1 failure mode. Sculptor was generating `App.tsx` with hallucinated page/component names that didn't match what other specialists actually produced. Two-pronged fix:
  1. **Sculptor prompt grounded in planned file list** — `App.tsx` generation now receives the full planned `file_paths` list from `shared_context` and is instructed to only import pages/components that appear in it.
  2. **App.tsx Reconciliation Pass** (new `worker.py` step 5a) — after ALL specialists finish, the worker reads the *actual* `src/pages/` and `src/components/` directories on disk, then regenerates `App.tsx` using only the real file names. This is the safety net that catches any remaining mismatches. Result: App.tsx can no longer reference a component that doesn't exist.
- **Framer-motion default import crash**: `import FramerMotion from 'framer-motion'` followed by `<FramerMotion.AnimatePresence>` is invalid. Sculptor's validate() hook now catches this pattern and forces a retry with the correct named-import form: `import { AnimatePresence, motion } from 'framer-motion'`.
- **Duplicate files in both `components/` and `pages/`**: Deep-crawl was using a naive `endswith("Page")` heuristic to decide which folder to put discovered components in, causing the same component to appear in both directories. Rewritten to: (1) prioritise explicit import paths (`from './pages/Foo'` → `pages/` folder), (2) only fall back to heuristics for bare JSX element names with no import path, and (3) skip components already generated under either folder.
- **`can_handle` glob matching too broad**: `src/components/*` was matching `src/components/ui/deep/Button.tsx` because `pattern[:-1]` just checked `startswith`. Now correctly distinguishes `/*` (single level) from `/**` (recursive).

### Added
- **9 production-grade skill files** covering the most common app domains. Each skill provides mandatory pages/routes, data model (with actual SQL), backend specifics, frontend specifics, and DTU integration notes. Skills are injected into all specialist prompts as domain expertise.
  - `booking-appointment.md` — Slot availability algorithm, booking wizard, DSGVO consent, AT phone validation
  - `healthcare-practice.md` — Patient records, SVNR hashing, DSGVO Art. 9, AES-256 at-rest encryption, Austrian Aufbewahrungspflicht
  - `ecommerce-store.md` — Product catalogue, cart, Stripe checkout, Austrian VAT breakdown, EU compliance
  - `saas-dashboard.md` — Multi-tenant, admin back-office, JWT auth flow, audit logs, Stripe webhooks
  - `cms-blog.md` — Post/author/category model, full-text search, RSS/sitemap, SEO meta, structured data
  - `task-project-management.md` — Kanban, fractional index reorder, WebSocket real-time, @mention notifications
  - `inventory-management.md` — Stock movements, FIFO valuation, barcode lookup, EAN-13, Austrian USt rates
  - `realtime-chat.md` — WebSocket events, typing indicators, Redis pubsub, virtual scrolling, unread counts
  - `iot-dashboard.md` — MQTT ingestion, timeseries telemetry, rule engine, SSE streaming, command dispatch
- **Professor skill router rewrite** — Replaced the vague "Analyze specs" prompt (which was fed the entire 50k-char specs and dumped a raw `os.listdir` into the prompt) with a compact static skill index. The LLM receives a table of `filename: one-line-description` entries and short specs (8k chars), making skill selection fast and reliable. Also stores `SKILL_FILE` in `shared_context` for traceability.

### Changed
- `worker.py` step numbering: old step 5 (Deep-Crawl) is now step 5b; new App.tsx Reconciliation Pass is step 5a. Progress percentages adjusted accordingly (reconciliation at 72%, deep-crawl at 75%+).
- `shared_context["file_paths"]` comment updated to note it is read by Sculptor for grounded App.tsx generation.

## [1.7.0] - 2025-02-08

### Added
- **REMOTE_CLIENT_DEMO.md**: Practical guide for demo/build at client site. Notebook (16GB, no GPU) + Tailscale + goliath server running Ollama. Goliath setup, notebook env vars, demo workflow, troubleshooting, offline fallback.
- **FULL_AUTO_DEPLOYMENT.md**: Gap analysis for full auto (domain, host, HTTPS, deploy). INWX API for .at, Hetzner API, Phase 1-3 roadmap. Not yet implemented.
- **MONETIZATION_PLAN.md**: €100 "Make My App" and €300 "Dark Factory + Support" products. Austrian small-company setup (Einzelunternehmen, Kleinunternehmer, Gewerbe). Landing page via meta-mcp. Non-tech packaging (ZIP, install.bat).

### Changed
- **README.md**: Added REMOTE_CLIENT_DEMO, FULL_AUTO_DEPLOYMENT, MONETIZATION_PLAN to docs list.
- **PRD.md**: Added Full Auto Deployment and Monetization to roadmap.
- **ASSESSMENT.md**: Updated file inventory, maturity, Last Updated.

## [1.6.0] - 2025-02-08

### Added
- **STRONGDM_ANALYSIS.md**: Documented analysis and comparison with [StrongDM Factory](https://factory.strongdm.ai). Methodology, economics ($1k/dev/day vs free), technique mapping, gaps (Pyramid Summaries, Semport).
- **Pyramid Summaries**: Deferred technique from StrongDM. Reversible multi-level context compression (2w, 4w, 8w, 16w) for specs/dependency context. Added to roadmap and NEXTSTEPS.

### Changed
- **PRD.md**: Added StrongDM attribution, updated roadmap with Pyramid Summaries as v2.0+ candidate.
- **ASSESSMENT.md**: Strategic positioning vs StrongDM, Pyramid Summaries gap, STRONGDM_ANALYSIS reference.
- **NEXTSTEPS.md**: Added Pyramid Summaries to Priority 3 (Phase 3+), reference to STRONGDM_ANALYSIS.
- **ARCHITECTURE.md**: Added Section 10 (Future Techniques) documenting Pyramid Summaries.
- **README.md**: StrongDM attribution, STRONGDM_ANALYSIS in docs list.

## [1.5.0] - 2025-02-08

### Added
- **SOTA Dashboard**: New web-based factory UI on `http://localhost:8002`. Features glassmorphic design, real-time status monitoring, and specialist execution visualization.
- **Real-Time Progress Tracking**: Standardized `ProgressTracker` singleton that reports build milestones (0-100%) from both the factory orchestrator and individual specialists.
- **Industrial Startup Protocol**: Robust implementation of `scripts/cleanup_zombies.ps1` integrated into `start_factory.ps1`. Automatically neutralizes processes blocking factory ports (8001, 8002) before launch.
- **Improved Logging Sync**: Synchronized singleton Logger initialization across the entire process tree to ensure all diagnostic data reaches the dashboard.

### Fixed
- **Port Blocking Issues**: Resolved the common problem of "Address already in use" errors during rapid development cycles.
- **Dashboard Progress Polling**: Implemented `/api/progress` endpoint for the frontend to reliably track long-running builds.

## [1.4.0] - 2026-02-08

### Added
- **DTU v0.2**: Complete rewrite of Digital Twin Universe with 9 mock services (Stripe, Auth, Email, SMS, Storage, Discord, Slack, Weather, Generic Webhook). Service registry at `/dtu/services`. Request audit log at `/dtu/log`. Deterministic always-succeed behavior.
- **DTU Integration Pipeline**: Factory starts DTU before Worker build. Judge receives `--dtu-url` argument. RunManifest injects DTU env vars (`STRIPE_API_URL`, `AUTH_API_URL`, etc.) into generated app's process environment.
- **DTU-Aware Code Generation**: Plumber specialist prompts now mandate env-var-based external API URLs for both Python (`os.environ.get(...)`) and Node (`process.env.X || default`). Generated apps never hardcode external URLs.
- **DTU Health Check**: Factory verifies DTU is actually responding (`/health`) after spinning it up, not just checking if the process is alive.

### Fixed
- **DTU completely disconnected from pipeline** (was HIGH severity, now resolved).
- **RunManifest stack detection**: Now detects `app.py` as Python entry point (previously only `main.py`).
- **DTU process cleanup**: Factory now calls `dtu.wait(timeout=5)` after terminate for clean shutdown.

## [1.3.0] - 2026-02-08

### Added
- **Propagandist Specialist**: New council member (18th specialist) that generates a full marketing/distribution kit: press release, blog post, social media kit (Twitter/LinkedIn/Instagram/Bluesky/Mastodon), email pitches (journalist/YouTuber/newsletter), Reddit posts, Discord announcements, Product Hunt launch kit, and a landing page HTML. Requires Shakespeare (copy) + Librarian (docs).
- **Vibe Enrichment**: New `foreman enrich` subcommand. LLM expands a terse vibe into a rich, domain-aware brief with suggested features, integrations, branding, pages, and workflows. User reviews `enriched_vibe.md` before proceeding to plan.
- **Landing Page Generation**: Factory pipeline now auto-generates `www/index.html` for every build (Step 5). Self-contained dark theme, glassmorphism, responsive. Runs even for API-only apps.
- **Context Injection**: `get_dependency_context()` in base Specialist. All specialists with `requires` now read upstream dependency output and inject it into their prompts (capped at 8000 chars).
- **Validation Hooks**: `validate()` method on base Specialist with domain-specific overrides: Plumber (server startup + /health), Sculptor (export statement), Registrar (JSON parse + package count), Morpheus (crypto imports), Librarian (markdown headers). Failed validation triggers retry with error injected.
- **Self-Declaration**: `declare_files()` method lets specialists inject files based on specs keywords. Plumber, Registrar, Nervos, Raggy, Morpheus, Amodei now declare their mandatory files.
- **Per-Specialist Temperature**: Each specialist has a tuned temperature (Plumber 0.15, Morpheus 0.1, Sculptor 0.4, Shakespeare 0.7, Propagandist 0.65, etc.). `LLMClient.generate()` accepts optional `temperature` parameter.
- **Stack-Aware New Specialists**: Nervos, Raggy, WebFinder, Archivist, Maestro, Auditor, Morpheus, Tesla, Amodei all branch Python vs Node prompts with framework-specific library recommendations.
- **Health Endpoint Mandate**: Plumber now requires GET /health for both Python (FastAPI) and Node (Express) backends.
- **API Docs Mandate**: FastAPI apps must keep /docs and /redoc active.

### Fixed
- **Async Foreman Bug**: `foreman.py` was calling `async generate()` without `await`. All three LLM functions are now properly `async def` with `await`, wrapped in `asyncio.run()`.
- **judge.py Indentation**: Fixed indentation error at line 62.
- **Validation retry**: Worker now has 3 attempts (up from 2) to accommodate both runt and validation retries.

### Changed
- **Worker retry logic**: Restructured to gate on runt detection first, then validation hook, using `continue` for cleaner flow.
- **Specialist count**: 12 -> 19 (18 domain specialists + Generalist).
- **Dependency graph**: 4 tiers -> Professor (0), bulk specialists (1), downstream specialists (2), Propagandist (3), Generalist (4).

## [1.2.0] - 2026-02-08

### Added
- **Multi-Stack Factory**: Vibe.md `## Tech Stack` section parsed into stack profile. Backend (python/fastapi, python/flask, python/django, node/express), Frontend (react, htmx, none), Database (postgresql, mysql, sqlite, mongodb).
- **Stack Profile Utilities**: `src/utils/stack_profile.py` with `parse_stack_from_vibe()`, `embed_in_specs()`, `extract_from_specs()`, `describe_stack()`.
- **Plumber dual-mode**: Python (FastAPI/Flask/Django) and Node (Express) prompts.
- **Sculptor dual-mode**: React and HTMX generation.
- **Registrar dual-mode**: requirements.txt/pyproject.toml for Python, package.json for Node, Dockerfile for both.
- **Deep-Crawl Python**: Scans Python imports (`from X import`, `import X`) in addition to TSX imports.

## [1.1.0] - 2026-02-08

### Added
- **Selectable App Stack**: Support for Python (FastAPI, Flask, Django) and Node.js backends.
- **Frontend Diversity**: Support for React, HTMX, and Svelte frontends.
- **HelpOracle**: Multilevel CLI help system (`foreman help`).
- **Advanced Logging**: Automated rotation and zip export components (`foreman log`).
- **Playwright Satisficer**: Live UI/API execution-based judging in `judge.py`.
- **Run Manifest**: Automated multi-component orchestration (`run_manifest.py`).
- **Git Manager**: Automated `git init` and initial commits for all builds.
- **Crawl v2**: Refined Deep-Crawl logic for component discovery.
- **GitHub Sync**: Initialized factory repo and linked to `sandraschi/dark-app-factory`.

### Changed
- **Async Council**: Specialist execution is now fully parallelized per dependency level.
- **Spec Injection**: Specialists now receive up to 50k chars of context to prevent skeletons.
- **Auditor Specialist**: Updated with advanced verification logic for Playwright integration.

### Fixed
- Specialist Council import regressions.
- File system "runt" detection (skeleton code prevention).
- Vibe-to-Stack parsing reliability.

## [1.0.0] - 2026-01-15
- Initial public release of the Dark App Factory methodology.

