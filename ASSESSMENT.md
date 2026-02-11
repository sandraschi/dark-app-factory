# Dark App Factory -- Deep Technical Assessment

**Assessor**: Claude Opus 4.6 (Cursor)
**Last Updated**: 2025-02-08
**Rounds Completed**: 6

---

## Executive Summary

Dark App Factory is a local-first software factory scaffold that uses cheap/local LLMs (Ollama) for code generation and expensive models for planning. The architecture is sound: Foreman plans, Worker Council generates in parallel, Satisficer judges with Playwright verification.

After 4 rounds of iterative improvement (Gemini 3 in Antigravity + Claude Opus 4.6 in Cursor), the project has evolved from a working prototype to a sophisticated multi-stack, multi-specialist system with proper logging, async execution, dependency-aware context injection, per-specialist validation, temperature tuning, self-declaring file generation, vibe enrichment, and a full marketing/distribution pipeline.

**Current maturity**: v1.7 -- Full pipeline with DTU, Dashboard, remote client demo docs, full auto deployment gap analysis, monetization plan.

**Strategic positioning**: Inspired by [StrongDM Factory](https://factory.strongdm.ai) (specs + scenarios -> agents -> validation). They target $1,000/dev/day in API tokens; we replicate the methodology for ~$0 using Ollama. See [STRONGDM_ANALYSIS.md](docs/STRONGDM_ANALYSIS.md).

---

## CRITICAL: Ollama Context Window Configuration

**Default Ollama context is 4,096 tokens. This is unusable for code generation.**

The specialists now inject up to 50,000 characters (~12,500 tokens) of specs plus up to 8,000 characters of upstream dependency context into prompts. With system prompt, anti-gaslighting protocol, skill data, and retry warnings, a single specialist call can easily exceed 20,000 tokens input.

**Minimum recommended**: 64,000 tokens (`num_ctx 65536`)
**Ideal for production**: 128,000 tokens if VRAM allows

### Configuration Methods

**Method 1: Environment variable (recommended for dev)**
```
set OLLAMA_CONTEXT_LENGTH=65536
ollama serve
```

**Method 2: Modelfile (recommended for reproducibility)**
```
FROM qwen2.5-coder:latest
PARAMETER num_ctx 65536
```
Then: `ollama create qwen2.5-coder-64k -f Modelfile`

### VRAM Budget (RTX 4090, 24GB)

| Model | Params | num_ctx 64k VRAM est. |
|-------|--------|-----------------------|
| qwen2.5-coder:7b | 7B | ~8-10 GB |
| qwen2.5-coder:14b | 14B | ~14-18 GB |
| llama3.1:8b | 8B | ~9-11 GB |
| deepseek-coder-v2:16b | 16B | ~16-20 GB |

---

## Architecture Overview (v1.3)

```
vibe.md  -->  [foreman enrich]  -->  enriched_vibe.md (user reviews)
                                        |
                                        v
          [foreman plan]  -->  specs/specs.md + scenarios/scenarios.md
                                        |
                                        v
                                 Worker (build)
                                   Tier 0: Professor (skills)
                                   Tier 1: Plumber, Sculptor, Nervos, Raggy, WebFinder,
                                           Archivist, Maestro, Auditor, Picasso, Registrar
                                   Tier 2: Librarian, Shakespeare, Morpheus, Tesla,
                                           Amodei, Houdini
                                   Tier 3: Propagandist (marketing/distribution)
                                   Tier 4: Generalist (catch-all)
                                   Deep-Crawl (missing imports, Python + TSX)
                                        |
                                        v
                                 Propagandist (landing page in factory.py)
                                        |
                                        v
                                 Judge (judge)
                                   |-- File inventory (os.walk)
                                   |-- Auditor specialist (static)
                                   |-- PlaywrightVerifier (runtime)
                                   |-- LLM verdict (PASS/FAIL)
                                        |
                                        v
                                 critique.md  -->  feeds back into next Foreman run
```

---

## What Works Well

1. **Economic split** -- Expensive model plans once, cheap model codes N times.
2. **Specialist Council** -- 18 domain specialists + Generalist with topological dependency ordering and parallel execution via `asyncio.gather`.
3. **Context Injection** -- Specialists with `requires` now read upstream dependency output via `get_dependency_context()`. Morpheus reads Plumber's routes; Houdini reads Sculptor's components; Amodei reads both.
4. **Validation Hooks** -- Domain-specific quality checks (Plumber: health endpoint, Sculptor: export statement, Registrar: JSON parse, Morpheus: crypto imports, Librarian: markdown headers). Failed validation triggers retry with error injected into prompt.
5. **Self-Declaration** -- Specialists declare files they need based on specs keywords via `declare_files()`. Ensures Morpheus fires if specs mention "auth", Raggy fires for "vector search", etc.
6. **Per-Specialist Temperature** -- Precision specialists (Plumber: 0.15, Morpheus: 0.1) get low temperature; creative specialists (Shakespeare: 0.7, Propagandist: 0.65, Picasso: 0.5) get high temperature.
7. **Multi-Stack** -- Python (FastAPI/Flask/Django), Node (Express), React, HTMX, or API-only. Stack parsed from `vibe.md`, embedded in `specs.md`, and routed through all specialists.
8. **Stack-Aware Specialists** -- All 7 new specialists (Nervos, Raggy, WebFinder, Archivist, Maestro, Morpheus, Tesla, Amodei, Auditor) branch Python vs Node prompts with framework-specific library recommendations.
9. **Deep-Crawl** -- Scans both TSX imports and Python imports. Skips stdlib and known third-party packages.
10. **Vibe Enrichment** -- `foreman enrich` uses LLM to expand terse vibe into rich domain brief. User reviews before proceeding.
11. **Propagandist** -- Full marketing pipeline: press release, blog post, social media kit, email pitches, Reddit/Discord/ProductHunt posts, landing page HTML. All grounded in actual specs.
12. **Landing Page** -- Factory step generates self-contained `www/index.html` with dark theme, glassmorphism, responsive design. Runs even for API-only apps.
13. **Async Throughout** -- All foreman/worker/judge functions are properly async with `asyncio.run()` at CLI entry points. Fixed pre-existing bug where foreman called async without await.
14. **Health Endpoints** -- Plumber mandates `/health` endpoint for both Python and Node backends.
15. **API Docs** -- FastAPI apps must keep `/docs` and `/redoc` active.

---

## Known Issues (Ordered by Severity)

### ~~HIGH: DTU Not Connected~~ FIXED (2026-02-08)

DTU v0.2 now has 9 mock services, a service registry (`/dtu/services`), and a request audit log (`/dtu/log`). Factory starts DTU before the build step. Plumber enforces env-var-based API URLs. RunManifest injects DTU env vars when booting the generated app. Judge passes `--dtu-url` to RunManifest.

### HIGH: RunManifest Default Layout Mismatch

`run_manifest.py` defaults to `npm start` in `server/` and `client/` subdirectories. But the factory generates flat structures. If no manifest.json exists in the output, `boot()` may fail.

### MEDIUM: Token Usage Never Reported

`LLMClient.get_usage()` exists but is never called. No aggregated cost reporting.

### MEDIUM: GitManager Exists But Is Unwired

`src/utils/git_manager.py` has `initialize()` and `commit_changes()` but nothing in the pipeline calls them.

### LOW: foreman.py Import Path Inconsistency

`foreman.py` uses `from utils.logger import logger` (relies on sys.path.append) while `worker.py` uses `from src.specialists.council import ...` (uses src. prefix).

### DEFERRED: Kitchen-Sink Dependencies

The Registrar hardcodes many npm/pip dependency groups regardless of vibe. Acceptable during dev. Must be whittled down before release.

### DEFERRED: Full Auto Deployment

Factory generates app only. No domain (INWX/nic.at), no Hetzner provisioning, no SSL, no deploy. See [FULL_AUTO_DEPLOYMENT.md](docs/FULL_AUTO_DEPLOYMENT.md). Phase 1: output deploy.sh. Phase 2: meta-mcp deploy tools. Phase 3: full auto.

### DEFERRED: Pyramid Summaries (StrongDM Technique)

StrongDM uses **Pyramid Summaries**: reversible summarization at multiple zoom levels (2 words, 4, 8, 16, etc.). Agents survey hundreds of items at compressed level, expand only interesting ones. Combines with MapReduce + Clustering. We use flat 50k char injection; no multi-resolution context. Would help when specs or file lists grow beyond context window.

---

## Round-by-Round Progress

| Issue | R1 | R2 | R3 | R4 | R5 | R6 |
|-------|----|----|-----|-----|-----|-----|
| Async LLM | Blocking | AsyncOpenAI | AsyncOpenAI | AsyncOpenAI + fixed await | AsyncOpenAI | Same |
| Parallel specialists | Sequential | asyncio.gather | asyncio.gather | asyncio.gather | asyncio.gather | Same |
| Specialist count | 12 | 12 | 12 | 19 | 19 | 19 |
| Context injection | None | None | None | **get_dependency_context()** | Same | Same |
| Validation hooks | None | None | None | **5 specialists** | Same | Same |
| Self-declaration | None | None | None | **7 specialists** | Same | Same |
| Temperature tuning | Fixed 0.2 | Fixed 0.2 | Fixed 0.2 | **Per-specialist** | Same | Same |
| Stack support | Node only | Node only | **Multi-stack** | Multi-stack | Multi-stack | Same |
| Vibe enrichment | None | None | None | **foreman enrich** | Same | Same |
| Marketing pipeline | None | None | None | **Propagandist** | Same | Same |
| Landing page | None | None | None | **www/index.html** | Same | Same |
| Token tracking | None | Tracked | Tracked | Tracked, not reported | Tracked, not reported | Same |
| Judge executes app | Fake | File list | **Playwright** | Playwright | **Playwright + DTU** | Same |
| Logging | None | None | **DarkLogger** | DarkLogger | DarkLogger | Same |
| Health endpoints | None | None | None | **Mandatory** | Mandatory | Same |
| API docs | None | None | None | **Mandatory** | Mandatory | Same |
| DTU connected | No | No | No | No | **Yes** | Yes |
| DTU services | 3 endpoints | 3 | 3 | 3 | **9 + registry** | Same |
| Kitchen-sink deps | Yes | Yes | Yes | Yes | Yes | Yes (deferred) |
| Remote client docs | No | No | No | No | No | **REMOTE_CLIENT_DEMO** |
| Full auto deploy | No | No | No | No | No | **Gap doc (roadmap)** |
| Monetization plan | No | No | No | No | No | **MONETIZATION_PLAN** |

---

## File Inventory

```
dark-app-factory/
  factory.py           # Orchestrator (async, landing page step)
  foreman.py           # Planner + enrich subcommand (async)
  worker.py            # Execution engine (async, parallel, validation, declare_files)
  judge.py             # Quality gate (Playwright, RunManifest)
  run_manifest.py      # Process orchestrator for generated apps
  questionnaire.py     # Human feedback loop
  vibe.md              # User intent input
  PRD.md               # Product requirements
  ASSESSMENT.md        # This file
  CHANGELOG.md         # Version history
  README.md            # Usage documentation
  .gitignore           # Comprehensive
  pyproject.toml       # Hatchling build system
  requirements.txt     # Python deps
  src/
    llm_client.py      # AsyncOpenAI with token tracking + temperature param
    auditor.py         # Playwright-based runtime auditor
    specialists/
      base.py          # Abstract Specialist (context injection, validation, declare_files, temperature)
      council.py       # 19 specialist implementations
    utils/
      logger.py        # DarkLogger singleton
      help_oracle.py   # Tiered help system
      git_manager.py   # Git init/commit (unwired)
      stack_profile.py # Multi-stack parsing/embedding
  dtu/
    main.py            # Digital Twin Universe (9 mocks, registry, audit log)
  docs/
    ARCHITECTURE.md    # System architecture doc
    META_MCP_INTEGRATION.md  # meta-mcp cross-utilization plan
    STRONGDM_ANALYSIS.md    # StrongDM Factory comparison, methodology, economics
    REMOTE_CLIENT_DEMO.md   # Practical use at client (notebook + Tailscale + goliath)
    FULL_AUTO_DEPLOYMENT.md # Gap: domain, host, HTTPS, deploy (roadmap)
    MONETIZATION_PLAN.md    # €100/€300 products, Austrian setup
  specs/               # Generated specs and research
  scenarios/           # Generated test scenarios
  skills/              # Domain knowledge files
  outputs/             # Generated app directories
```
