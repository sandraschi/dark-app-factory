# Changelog

All notable changes to the Dark App Factory will be documented in this file.

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
