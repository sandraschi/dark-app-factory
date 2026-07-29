# Dark App Factory -- Next Steps (Gemini Handover)

> **OBSOLETE (2026-07-30).** Written 2026-02-09 during the Gemini session. Superseded by
> [reports/deep-assess-2026-07-29.md](reports/deep-assess-2026-07-29.md), which reflects the
> current state of the code. Kept for history.
>
> What has changed since this document was written:
> - 1.1 RunManifest default layout: DONE. `write_manifest_from_output()` writes
>   `manifest.json` after the build.
> - 1.2 Wire GitManager: DONE. `factory.py` calls `initialize()` and `commit_changes()`.
> - 1.3 Token usage reporting: DONE. `get_usage_summary()` is logged at end of run.
> - 1.4 subprocess for Worker/Judge: DONE. Both are direct async calls now.
> - 2.2 Dynamic dependency selection: PARTIAL. `Registrar.validate()` gates unjustified
>   deps via `GATED_DEPS`, but nothing checks for *missing* ones. That is the open blocker.
> - 2.3 Normalize import paths: DONE. All entry points set `sys.path` consistently.
> - 2.4 Cross-platform kill zombies: DONE, then rewritten in 0.2.1-beta. Now lives in
>   `src/utils/ports.py` and covers the ports the system actually binds.
> - 4.3 Test suite: DONE. 135 tests, plus `tests/test_boot_path.py`.
> - Still open and still correct: 2.1 DTU request verification in Judge, 3.1 WebSockets,
>   3.2 dependency graph visualisation, 3.3 feedback loop automation, 3.4 multi-run
>   convergence, 3.6 full auto deployment, 3.7 Pyramid Summaries.
> - Note also: 3.3 "Feedback Loop Automation" understates a defect. `questionnaire.py`
>   appends feedback into `vibe.md`, mutating the user's own input file. `vibe.md` in this
>   repo is currently corrupted as a result.

**Author**: Gemini 3 (Antigravity)
**Date**: 2026-02-09
**Context**: Continuing the Dark App Factory build-out.

---

## What Was Done Recently (Gemini Session)

### Round 6: Factory Dashboard & Operational Resilience
- **SOTA Dashboard**: Built `web/server.py` and `web/index.html` featuring real-time build monitoring.
- **Progress Protocol**: Implemented thread-safe `ProgressTracker` singleton for high-fidelity build feedback.
- **Zombie Cleanup**: Created `scripts/cleanup_zombies.ps1` to neutralize port-blocking processes.
- **Industrial Startup**: Optimized `start_factory.ps1` for robust, one-command deployment.
- **Unified Logging**: Synchronized `DarkLogger` across the orchestrator and dashboard.

### Round 5: DTU Integration (The Big Fix)
- Rewrote `dtu/main.py` with 9 mock services + service registry + audit log
- Plumber now mandates env-var-based external API URLs (Python + Node)
- RunManifest accepts `dtu_url`, injects env vars into child processes
- Factory starts DTU BEFORE build, passes `--dtu-url` to judge
- Judge passes DTU URL to RunManifest during Playwright testing
- Full DTU pattern explained in ARCHITECTURE.md Section 7

### Documentation Updates
- CHANGELOG.md: v1.5 entries for Dashboard and Startup Protocol.
- README.md: v1.5 rewrite with Dashboard and Startup sections.
- ARCHITECTURE.md: Added Section 8 (Monitoring) and Section 9 (Resilience).
- WALKTHROUGH.md: Detailed guide for the progress tracking implementation.
- **STRONGDM_ANALYSIS.md** (2026-02-09): Analysis of [StrongDM Factory](https://factory.strongdm.ai). Methodology, $1k/dev/day economics, technique mapping, Pyramid Summaries explained.

---

## Priority 1: Critical (Must Fix)

### 1.1 RunManifest Default Layout
**File**: `run_manifest.py`
**Issue**: When no `manifest.json` exists, RunManifest detects Python or Node but the entry file assumptions may be wrong. Currently checks `main.py`, `app.py`, `server.js` but the actual generated entry point depends on which files the Plumber generated.
**Fix**: After worker build completes, write a `manifest.json` into the output dir with the correct entry points. Worker knows what it generated.

### 1.2 Wire GitManager
**File**: `src/utils/git_manager.py`, `factory.py`
**Issue**: `GitManager` has `initialize()` and `commit_changes()` but nothing calls them.
**Fix**: In `factory.py`, after successful worker build:
```python
from src.utils.git_manager import GitManager
gm = GitManager(output_dir)
gm.initialize()
gm.commit_changes("Initial factory build")
```
After judge PASS: `gm.commit_changes("Passed quality gate")`

### 1.3 Token Usage Reporting
**File**: `src/llm_client.py`, `factory.py`
**Issue**: `LLMClient` tracks `tokens_used` dict but `get_usage()` / `get_usage_summary()` is never called.
**Fix**: At end of `factory.py` run, collect usage from all LLMClient instances. Print summary with estimated cost.

### 1.4 factory.py Still Uses subprocess for Worker/Judge
**File**: `factory.py`
**Issue**: Worker and Judge are invoked via `subprocess.run()`, which means token usage from their LLMClient instances is lost (separate processes).
**Fix**: Import and call `worker.run_factory()` and `judge.run_judgement()` directly as async functions within factory.py. This enables shared state and aggregated token reporting.

---

## Priority 2: Important Improvements

### 2.1 DTU Request Verification in Judge
**File**: `judge.py`
**Issue**: DTU logs all requests to `/dtu/log`, but judge never checks if the generated app actually called the expected endpoints.
**Fix**: After Playwright testing, query `GET {dtu_url}/dtu/log`. Check that expected services were called (e.g., if specs mention payments, verify Stripe endpoints were hit). Include in audit report.

### 2.2 Dynamic Dependency Selection (Registrar)
**File**: `src/specialists/council.py` (Registrar class)
**Issue**: Registrar hardcodes 35+ npm packages / pip packages for every app regardless of vibe. Wastes bandwidth and install time.
**Fix**: Analyze specs keywords to select relevant dependency groups. E.g., if no "3D" or "three" in specs, skip Three.js. If no "audio", skip Tone.js/pydub.

### 2.3 Normalize Import Paths
**Files**: All Python files
**Issue**: `foreman.py` uses `sys.path.append` + `from utils.logger import logger`. `worker.py` uses `from src.specialists.council import ...`. Inconsistent.
**Fix**: Pick one convention. Recommended: always use `src.` prefix and ensure `PYTHONPATH` or `sys.path` is set once at entry point.

### 2.4 Cross-Platform Kill Zombies
**File**: `factory.py`
**Issue**: `kill_zombies()` uses `netstat -ano | findstr LISTENING` and `taskkill /F /PID` -- Windows only.
**Fix**: Add `sys.platform` check. On Linux/macOS use `lsof -i :PORT` and `kill -9 PID`.

---

## Priority 3: Feature Enhancements

### 3.1 WebSocket Implementation
**Issue**: Dashboard currently relies on HTTP polling for progress. Scalability and latency suboptimal.
**Fix**: Switch to `WebSockets` or `Server-Sent Events (SSE)` for real-time log streaming and progress updates.

### 3.2 Visual Dependency Graph
**Issue**: Specialist Council tiers are hard to visualize.
**Fix**: Implement a Mermaid.js or D3.js visualization in the dashboard showing the parallel tiers and dependency injection paths.

### 3.3 Specialist: Registrar Writes manifest.json
The Registrar already generates `package.json` / `requirements.txt`. It should also generate a `manifest.json` for RunManifest:
```json
{
  "components": [
    {"name": "backend", "command": "python main.py", "cwd": "."},
    {"name": "frontend", "command": "npm run dev", "cwd": "."}
  ]
}
```

### 3.2 DTU Extension: More Services
Add mocks for:
- **Google Maps / Geocoding** -- `MAPS_API_URL`
- **OpenAI / Ollama** -- `LLM_API_URL` (for apps that themselves call LLMs)
- **AWS SES / SendGrid** -- `SENDGRID_API_URL`
- **Twilio** -- `TWILIO_API_URL`
- **Firebase Auth** -- `FIREBASE_AUTH_URL`

### 3.3 Feedback Loop Automation
`questionnaire.py` currently requires human input. Make it optional:
- `factory.py run --auto` skips questionnaire
- `factory.py run --feedback` launches it

### 3.4 Multi-Run Convergence
The PRD mentions iterative convergence (critique -> fix loop). Currently:
- Judge writes `critique.md` on FAIL
- Foreman can read `critique.md` to adjust specs
- But this loop is manual

Automate: if judge FAILs, re-run foreman with critique, then re-run worker, up to N iterations.

### 3.5 meta-mcp Agent Integration
See `docs/META_MCP_INTEGRATION.md` for the plan. The idea: expose factory phases (plan, build, judge) as meta-mcp agents that can be started, polled, and awaited.

### 3.6 Full Auto Deployment (Domain + Host + HTTPS)
**Docs**: `docs/FULL_AUTO_DEPLOYMENT.md`
**Gap**: Factory generates app only. No domain registration, no Hetzner provisioning, no SSL, no deploy.
**Phase 1**: Output `deploy.sh` + `deploy_config.example.yaml`. User runs with INWX + Hetzner API keys.
**Phase 2**: meta-mcp deploy tools. Optional auto-deploy.
**Phase 3**: Full auto: INWX domain + Hetzner + Certbot/Cloudflare SSL. User provides keys once.

### 3.7 Pyramid Summaries (StrongDM Technique)
**Source**: [factory.strongdm.ai/techniques/pyramid-summaries](https://factory.strongdm.ai/techniques/pyramid-summaries)
**What**: Reversible summarization at multiple zoom levels (2 words, 4, 8, 16, etc.). Agents survey hundreds of items at compressed level, expand only interesting ones. Combines with MapReduce + Clustering.
**Where it helps**: Specs injection (when >50k chars), dependency context (when >8k chars), scenarios (survey many, run subset). We use flat 50k injection today.
**When to implement**: When hitting context overflow, or building apps with 50+ files. See `docs/STRONGDM_ANALYSIS.md`.

---

## Priority 4: Polish

### 4.1 Whittling Kitchen-Sink Imports
Once the factory is stable, audit all specialist imports and remove unused ones. The `base.py` import of `json` and `re` is fine (used in validation). But council.py imports should be reviewed.

### 4.2 .env.example
Create a `.env.example` with all required/recommended env vars:
```
FOREMAN_MODEL=llama3.1:latest
FOREMAN_BASE_URL=http://localhost:11434/v1
WORKER_MODEL=qwen2.5-coder:latest
WORKER_BASE_URL=http://localhost:11434/v1
OLLAMA_CONTEXT_LENGTH=65536
DTU_PORT=8001
```

### 4.3 Test Suite
No tests exist. Priority for testing:
1. `stack_profile.py` -- pure functions, easy to test
2. `base.py` -- `can_handle()`, `get_dependency_context()`, `validate()`
3. `dtu/main.py` -- start server, hit endpoints, verify responses
4. `run_manifest.py` -- `_detect_stack()` with mock directories

### 4.4 Remaining Rich Markup in Logs
Check for any remaining `[bold yellow]...[/bold yellow]` Rich markup tags in logger calls. They should be plain text. One known instance was in `judge.py` (fixed) but scan all files.

---

## File Map (Quick Reference)

```
factory.py           -- Pipeline orchestrator (DTU lifecycle, subprocess calls)
foreman.py           -- Planner (plan, enrich, research, help, log subcommands)
worker.py            -- Execution engine (specialist council, parallel, validation)
judge.py             -- Quality gate (Playwright, RunManifest, LLM verdict)
run_manifest.py      -- Process boot orchestrator (DTU env injection)
questionnaire.py     -- Human feedback loop
dtu/main.py          -- Digital Twin Universe (9 mock services)
src/llm_client.py    -- AsyncOpenAI wrapper (temperature, token tracking)
src/auditor.py       -- Playwright-based runtime auditor
src/specialists/
  base.py            -- Abstract Specialist (context injection, validation, declare_files)
  council.py         -- 19 specialist implementations
src/utils/
  logger.py          -- DarkLogger singleton
  help_oracle.py     -- Tiered help system
  git_manager.py     -- Git init/commit (UNWIRED -- see 1.2)
  stack_profile.py   -- Multi-stack parsing/embedding
```

---

## Notes for Gemini

- All Python files parse cleanly (verified with `py_compile`).
- No test suite exists yet. Be careful with refactors.
- The `logger.success()` and `logger.audit()` methods are custom extensions on the DarkLogger. Standard logging does not have these.
- Worker calls specialists via `specialist.generate(file_path, specs, shared_context, worker_llm)`. The signature is `(self, file_path, specs, shared_context, worker)` where worker is the LLMClient.
- Specialist `generate()` in base.py has a DIFFERENT signature `(self, specs, shared_context)` from the actual implementations. The base class abstract method is not enforced. This is a known inconsistency -- the actual implementations all use the 4-arg signature.
- `OLLAMA_CONTEXT_LENGTH=65536` is mandatory. Default 4096 will cause truncated/garbage output.
- DTU is on port 8001 by default. Change via `DTU_PORT` env var.
