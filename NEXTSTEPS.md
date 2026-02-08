# Dark App Factory -- Next Steps (Gemini Handover)

**Author**: Claude Opus 4.6 (Cursor)
**Date**: 2026-02-08
**Context**: Handing over to Gemini 3 (Antigravity) for continued development.

---

## What Was Done Today (Opus Session)

### Round 4: Specialist Council Sophistication
- Added `get_dependency_context()` to base.py -- specialists read upstream output
- Added `validate()` hooks on Plumber, Sculptor, Registrar, Morpheus, Librarian
- Added `declare_files()` on Plumber, Registrar, Nervos, Raggy, Morpheus, Amodei
- Per-specialist temperature tuning (0.1 to 0.7)
- Stack-aware prompts on all new specialists (Python + Node branches)
- Worker retry logic: 3 attempts, validation failure injects error into retry prompt

### Round 4b: Vibe Enrichment
- `foreman enrich` subcommand: LLM expands terse vibe into rich domain brief
- Writes `enriched_vibe.md` for user review before `foreman plan`
- Fixed async/await bug in foreman.py (was calling async without await)

### Round 4c: Propagandist
- New 18th specialist: generates press release, blog, social media, email pitches, Reddit, Discord, Product Hunt posts
- Requires Shakespeare + Librarian. Temperature 0.65
- Landing page generation integrated into factory.py (Step 6)

### Round 5: DTU Integration (The Big Fix)
- Rewrote `dtu/main.py` with 9 mock services + service registry + audit log
- Plumber now mandates env-var-based external API URLs (Python + Node)
- RunManifest accepts `dtu_url`, injects env vars into child processes
- Factory starts DTU BEFORE build, passes `--dtu-url` to judge
- Judge passes DTU URL to RunManifest during Playwright testing
- Full DTU pattern explained in ARCHITECTURE.md Section 7

### Documentation Updates
- ASSESSMENT.md: Round 5 with progress matrix
- CHANGELOG.md: v1.2, v1.3, v1.4 entries
- README.md: Full rewrite with specialist table, DTU section, quick start
- PRD.md: Updated to v1.3 architecture
- ARCHITECTURE.md: Complete rewrite with 7 sections including DTU deep dive
- mcp-central-docs: New `docs/projects/dark-app-factory/STATUS.md`

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

### 2.5 factory.py Still Uses subprocess for Worker/Judge
**File**: `factory.py`
**Issue**: Worker and Judge are invoked via `subprocess.run()`, which means token usage from their LLMClient instances is lost (separate processes).
**Fix**: Import and call `worker.run_factory()` and `judge.run_judgement()` directly as async functions within factory.py. This enables shared state and aggregated token reporting.

---

## Priority 3: Feature Enhancements

### 3.1 Specialist: Registrar Writes manifest.json
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
