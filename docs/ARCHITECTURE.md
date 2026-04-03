# Dark App Factory Architecture

**Last Updated**: 2026-02-09 | **Version**: 1.5

Dark App Factory is a parallelized generation pipeline designed to produce web applications from high-level prompts using local LLMs.

## 1. Core Philosophy
- **Verification-first**: Rigorous verification (Judge) ensures generated code matches observed technical reality. Prompts include explicit pressure against skeleton code, placeholders, and TODO stubs.
- **Requirements-first**: Code is treated as executable output, and design follows functional requirements.
- **High-Fidelity**: No skeletons. No placeholders. Every file is generated as production-ready logic.
- **Distribution by Default**: Every app ships with a marketing kit and landing page.

## 2. Pipeline Overview

```
vibe.md  -->  [foreman enrich]  -->  enriched_vibe.md (user reviews)
                                        |
                                        v
          [foreman plan]  -->  specs.md + scenarios.md (with stack profile)
                                        |
                                        v
                                 Worker Council (build)
                                   Tier 0: Professor
                                   Tier 1: Plumber, Sculptor, Nervos, Raggy, WebFinder,
                                           Archivist, Maestro, Auditor, Picasso, Registrar
                                   Tier 2: Librarian, Shakespeare, Morpheus, Tesla,
                                           Amodei, Houdini
                                   Tier 3: Propagandist
                                   Tier 4: Generalist (catch-all)
                                   Deep-Crawl (missing imports)
                                        |
                                        v
                                 Landing Page (factory.py Step 6)
                                        |
                                        v
                                 Judge (Playwright + LLM verdict)
                                   |-- App booted via RunManifest with DTU env vars
                                   |-- All external API calls route to DTU mocks
                                   |-- Playwright verifies UI/API against scenarios
```

**DTU lifecycle**: The Digital Twin Universe starts *before* the Worker build (Step 4) and remains alive through Judge (Step 7). RunManifest injects DTU env vars (`STRIPE_API_URL`, `AUTH_API_URL`, etc.) into the generated app's process environment, so the app talks to DTU mocks instead of real external services.

## 3. Component Hierarchy

### Foreman (`foreman.py`)
- **Role**: Architect, Planner, Enricher.
- **Subcommands**: `plan`, `enrich`, `research`, `help`, `log`.
- **Enrich**: LLM expands terse vibe into rich domain brief. User reviews before planning.
- **Plan**: Converts vibe into specs with embedded stack profile.
- **Oracle**: Leverages search data for 2026-standard compliance.
- **Documentation**: Hosts the Help Oracle multilevel documentation system.

### Worker (`worker.py`)
- **Role**: Execution Engine.
- **Specialist Council**: Orchestrates 19 domain-specific AI Specialists.
- **Parallel Pipeline**: Executes specialist tasks in dependency-aware tiers via `asyncio.gather`.
- **Deep-Crawl**: Recursively scans generated code to find and implement missing components (TSX + Python imports).
- **Validation**: Runs specialist-specific `validate()` after generation. Retries with error injection on failure.
- **Self-Declaration**: Calls `declare_files()` per specialist to inject keyword-triggered mandatory files.

### Judge (`judge.py`)
- **Role**: Quality gate.
- **Verification**: Live UI/API audits using Playwright.
- **Verdict**: PASS/FAIL with `critique.md` feedback loop.

### Factory (`factory.py`)
- **Role**: Full Pipeline Orchestrator.
- **Steps**: Research -> Plan -> DTU -> Build -> Landing Page -> Judge -> Launch.
- **Landing Page**: Generates self-contained `www/index.html` using Foreman LLM.
- **DTU Lifecycle**: Starts DTU before build, passes `DTU_URL` to judge, shuts down DTU after all steps complete.

### Digital Twin Universe (`dtu/main.py`)
- **Role**: Local service emulator replacing external APIs during testing.
- **Port**: Configurable via `DTU_PORT` env var (default 8001).
- **Service Registry**: `GET /dtu/services` returns all mock URLs and corresponding env vars.
- **Request Log**: `GET /dtu/log` returns the last N requests for debugging.
- **Mock Services**: Stripe, Auth, Email, SMS, Storage, Discord, Slack, Weather, Webhook, LLM (OpenAI/Anthropic), Google Calendar, Google Maps (geocoding), Analytics, Puzzles (PuzzlePhil-style), TikTok, YouTube.
- **Deterministic**: Endpoints return predictable responses for repeatable integration tests without external dependencies.

### Utils & Core Logic
- **LLMClient (`llm_client.py`)**: AsyncOpenAI with token tracking. Accepts per-call `temperature` override.
- **Stack Profile (`stack_profile.py`)**: Multi-stack parsing/embedding (Node/Python, React/HTMX).
- **Git Manager (`git_manager.py`)**: Automated repository initialization and build versioning.
- **Run Manifest (`run_manifest.py`)**: Multi-component boot orchestrator. Stack-aware. Accepts `dtu_url` parameter and injects DTU env vars into child process environment.
- **DarkLogger (`logger.py`)**: Singleton logging with rotation (5MB, 5 backups) and Rich console output.
- **Help Oracle (`help_oracle.py`)**: Tiered (basic to expert) on-demand documentation.

## 4. Specialist Council (19 Members)

### Tier 0 (Foundation)
| Specialist | Domain | Temp | Requires | Key Feature |
|---|---|---|---|---|
| Professor | Skill battery injection | 0.2 | - | Domain knowledge seeding |

### Tier 1 (Core Builders)
| Specialist | Domain | Temp | Requires | Key Feature |
|---|---|---|---|---|
| Plumber | Backend (Python/Node) | 0.15 | Professor | `/health` mandate, validate(server startup), declare_files(routers/schemas) |
| Sculptor | Frontend (React/HTMX) | 0.4 | Professor | validate(export stmt), dep_context from Professor |
| Registrar | Infrastructure (deps, Docker) | 0.1 | - | validate(JSON parse, pkg count), declare_files(requirements/Dockerfile/vite) |
| Nervos | Heartbeat, messaging, plugins | 0.2 | - | Python: BackgroundTasks, python-telegram-bot. Node: socket.io |
| Raggy | RAG, vector search, embeddings | 0.2 | - | Python: chromadb, langchain, FAISS. declare_files(retriever/embeddings) |
| WebFinder | Web scraping, APIs | 0.2 | - | Python: httpx, BeautifulSoup4, feedparser |
| Archivist | ePub/PDF/Mobi parsing | 0.2 | - | Python: ebooklib, PyPDF2/pdfplumber |
| Maestro | Audio, music | 0.3 | - | Python: pydub, librosa, mido. Node: Tone.js |
| Auditor | Excel/Word, data validation | 0.2 | - | Python: openpyxl, python-docx, pandas |
| Picasso | SVG, illustrations | 0.5 | - | Inline SVG orchestration |

### Tier 2 (Downstream)
| Specialist | Domain | Temp | Requires | Key Feature |
|---|---|---|---|---|
| Librarian | Documentation, README | 0.6 | Plumber | validate(markdown headers), dep_context from Plumber |
| Shakespeare | Marketing copy, content | 0.7 | - | Narratives, SEO, in-app copy |
| Morpheus | Security, auth, encryption | 0.1 | Plumber | validate(crypto imports), declare_files(middleware/crypto), dep_context from Plumber routes |
| Tesla | Robotics, IOT, ROS | 0.15 | Nervos | Python: rclpy, paho-mqtt, python-osc, pyserial. dep_context from Nervos |
| Amodei | AI/LLM integration, Ollama | 0.3 | Plumber, Sculptor | Python: Ollama client, SSE, httpx streaming. declare_files(llm_client/streaming/ChatFloater) |
| Houdini | Animations, Three.js | 0.45 | Sculptor | Framer Motion, GSAP. dep_context from Sculptor components |

### Tier 3 (Distribution)
| Specialist | Domain | Temp | Requires | Key Feature |
|---|---|---|---|---|
| Propagandist | Marketing distribution | 0.65 | Shakespeare, Librarian | 8 platform-specific assets: press release, blog, social, email, Reddit, Discord, PH, landing page |

### Tier 4 (Catch-All)
| Specialist | Domain | Temp | Requires | Key Feature |
|---|---|---|---|---|
| Generalist | Everything unmatched | 0.3 | All above | Catches files not owned by any specialist |

## 5. Sophistication Mechanisms

### Context Injection
`base.py` provides `get_dependency_context(shared_context)`. Extracts outputs from `requires` specialists, capped at 8000 chars. Injected into prompts under "UPSTREAM CONTEXT" heading.

### Validation Hooks
`base.py` provides `validate(file_path, code, specs)` returning `(bool, str)`. Worker retries up to 3 times if validation fails, injecting the error message into the retry prompt.

### Self-Declaration
`base.py` provides `declare_files(specs, stack_profile)` returning `List[str]`. Worker calls this after initial planning and adds declared files to the generation queue. Keyword-based: if specs mention "auth", Morpheus declares security files.

### Temperature Tuning
Each specialist passes its `temperature` to `LLMClient.generate()`. Deterministic specialists (Plumber: 0.15, Morpheus: 0.1, Registrar: 0.1) produce reliable, reproducible output. Creative specialists (Shakespeare: 0.7, Propagandist: 0.65) produce diverse, engaging content.

### Multi-Stack Routing
All specialists check `stack_profile["backend"]` and `stack_profile["frontend"]` to branch their prompts. Python backends get FastAPI/Flask/Django patterns with appropriate imports (uvicorn, flask, django). Node backends get Express/middleware patterns.

## 6. Reliability Enhancements
- **Context Hardening**: All specialists receive up to 50,000 chars of specs + 8,000 chars of upstream context.
- **Anti-Runt Logic**: Generated code < 50 chars triggers immediate retry with escalated pressure.
- **Anti-Gaslighting Protocol**: Explicit prompt instructions forbidding skeleton code, placeholder functions, pass stubs.
- **Structured Logging**: DarkLogger with rotation ensures all operations are persistent and auditable.
- **Health Mandate**: Every backend must expose GET /health.
- **API Docs**: FastAPI backends must keep /docs and /redoc active.

## 7. Digital Twin Universe (DTU) -- Technical Deep Dive

### The Pattern

The Digital Twin is a well-established pattern in industrial engineering (Industry 4.0, NASA, automotive). The concept: create a local, deterministic replica of external services so that the system under test operates in a fully controlled environment. No network calls, no API keys, no rate limits, no cost.

In the context of the Dark App Factory, the DTU replaces every external API dependency (payments, auth, email, storage, etc.) with a local FastAPI server that always succeeds. This allows the Satisficer (Judge) to boot and test the generated app without requiring real Stripe keys, real email providers, or real auth0 accounts.

### How It Works

```
                        PRODUCTION                    TESTING (with DTU)
                        ---------                     ------------------
Generated App           Generated App
    |                       |
    | STRIPE_API_URL=       | STRIPE_API_URL=
    | https://api.stripe    | http://localhost:8001/stripe
    |                       |
    v                       v
Stripe API (real)       DTU Mock (local, always succeeds)
```

The key mechanism is **environment variable injection**:

1. **Plumber Specialist** generates code that reads ALL external API URLs from env vars:
   - Python: `os.environ.get("STRIPE_API_URL", "https://api.stripe.com")`
   - Node: `process.env.STRIPE_API_URL || "https://api.stripe.com"`
   - Default values are the real production URLs.

2. **DTU Server** (`dtu/main.py`) starts on port 8001 (configurable via `DTU_PORT`) and exposes mock endpoints for 9 services.

3. **RunManifest** receives `dtu_url` parameter. When booting the generated app, it injects env vars:
   ```
   STRIPE_API_URL=http://localhost:8001/stripe
   AUTH_API_URL=http://localhost:8001/auth
   EMAIL_API_URL=http://localhost:8001/email
   SMS_API_URL=http://localhost:8001/sms
   STORAGE_API_URL=http://localhost:8001/storage
   DISCORD_WEBHOOK_URL=http://localhost:8001/discord
   SLACK_WEBHOOK_URL=http://localhost:8001/slack
   WEATHER_API_URL=http://localhost:8001/weather
   WEBHOOK_URL=http://localhost:8001/webhook
   ```

4. **Factory** starts DTU *before* the Worker build and keeps it alive through Judge.

5. **Judge** passes `--dtu-url` to RunManifest so the generated app connects to DTU during Playwright testing.

### Service Registry

DTU exposes `GET /dtu/services` which returns the full registry:

```json
{
    "dtu_version": "0.2.0",
    "port": 8001,
    "services": {
        "stripe": {"base_url": "http://localhost:8001/stripe", "env_var": "STRIPE_API_URL"},
        "auth": {"base_url": "http://localhost:8001/auth", "env_var": "AUTH_API_URL"},
        ...
    },
    "env_vars": {
        "STRIPE_API_URL": "http://localhost:8001/stripe",
        "AUTH_API_URL": "http://localhost:8001/auth",
        ...
    }
}
```

This allows programmatic discovery -- a future meta-mcp agent could query the registry and configure services dynamically.

### Request Audit Log

DTU logs all incoming requests to an in-memory buffer. `GET /dtu/log?limit=50` returns the last N entries. This is useful for the Judge to verify that the generated app actually called the expected external APIs during testing.

### Mock Behavior

All mocks are **deterministic and always succeed**:
- Stripe: Payments always return `status: succeeded`
- Auth: Login always returns a valid mock JWT
- Email/SMS: Always return `status: sent`/`status: delivered`
- Storage: Upload always returns a mock URL
- Webhooks: Always return `received: true`

This is intentional. The DTU tests *integration logic* (does the app call Stripe when a payment is submitted?), not *external service behavior* (does Stripe actually charge the card?). The latter requires real integration tests with live APIs.

### Extending DTU

To add a new mock service:

1. Add the endpoint to `dtu/main.py`:
   ```python
   @app.post("/newservice/endpoint")
   async def new_endpoint(request: Request):
       return {"status": "ok", "id": f"ns_{uuid.uuid4().hex[:12]}"}
   ```

2. Add it to the `SERVICE_REGISTRY` dict in `dtu/main.py`.

3. Add the env var to `DTU_ENV_VARS` in `run_manifest.py`.

4. Add the env var instruction to Plumber's prompt in `council.py`.

5. The generated app will automatically use the mock during testing.
259: 
260: ## 8. Monitoring & Progress Layer
261: 
262: The factory implements a thread-safe, singleton-based monitoring system via `src.utils.progress.ProgressTracker`.
263: 
264: ### Progress Tracking
265: - **Milestones**: The pipeline registers major milestones (Planning, Building, Judging) with defined weighting.
266: - **Specialist Tracking**: Each specialist reports its own status (PENDING, RUNNING, DONE, FAILED) and the files it generates.
267: - **API Integration**: The `ProgressTracker` state is exposed via the `/api/progress` endpoint on the dashboard.
268: 
269: ### Dashboard Real-Time Feed
270: The Dashboard UI (`web/index.html`) polls the progress API to provide a glassmorphic visualization of the "Factory Floor," showing exactly where the bottlenecks are in the specialist tiers.
271: 
272: ## 9. Operational Resilience
273: 
274: Dark App Factory is designed for high-industrial availability.
275: 
276: ### Industrial Startup Protocol
277: - **Zombie Neutralization**: Before starting, the factory runs `scripts/cleanup_zombies.ps1` to force-kill any processes listening on the internal service ports (8001 for DTU, 8002 for Dashboard).
278: - **Auto-Installer**: `start_factory.ps1` ensures all dependencies are present and the environment is clean before initializing the LLM engine.
279: 
280: ### Singleton Synchronization
281: To prevent state fragmentation, the `DarkLogger` and `ProgressTracker` use a shared initialization pattern, ensuring that logs from sub-processes (Worker/Judge) are unified in the primary log files and available to the dashboard.

## 10. Future Techniques (StrongDM-Inspired)

### Pyramid Summaries (Deferred)

**Source**: [factory.strongdm.ai/techniques/pyramid-summaries](https://factory.strongdm.ai/techniques/pyramid-summaries)

Reversible summarization at multiple zoom levels. E.g. "Summarize this spec section in 2 words. Now 4. Now 8. Now 16." Each level preserves meaning while expanding/contracting detail. Agents survey many items at compressed level, expand only relevant ones. Combines with MapReduce + Clustering.

**Current state**: We use flat 50k char injection for specs and 8k cap for dependency context. No multi-resolution compression.

**When to add**: Context overflow, large specs (10+ pages), 50+ file outputs, or "survey N scenarios, run subset" without loading all N. See `docs/STRONGDM_ANALYSIS.md`.
