# Dark App Factory -- Deep Technical Assessment

**Assessor**: Claude Opus 4.6 (Cursor)
**Last Updated**: 2026-02-08
**Rounds Completed**: 3

---

## Executive Summary

Dark App Factory is a local-first software factory scaffold that uses cheap/local LLMs (Ollama) for code generation and expensive models for planning. The architecture is sound: Foreman plans, Worker Council generates in parallel, Satisficer judges with Playwright verification.

After 3 rounds of iterative improvement (Gemini 3 in Antigravity), the project has evolved from a working prototype to a structurally coherent system with proper logging, async execution, execution-based quality gates, and context hardening.

**Current maturity**: v0.3 -- Functional pipeline with real verification.

---

## CRITICAL: Ollama Context Window Configuration

**Default Ollama context is 4,096 tokens. This is unusable for code generation.**

The specialists now inject up to 50,000 characters (~12,500 tokens) of specs into prompts. With system prompt, anti-gaslighting protocol, skill data, and retry warnings, a single specialist call can easily exceed 15,000 tokens input.

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

**Method 3: Per-request (requires code change in LLMClient)**
Pass `num_ctx` in the API call options. The OpenAI-compatible API does not natively support this; requires Ollama-specific parameter passing.

### VRAM Budget (RTX 4090, 24GB)

| Model | Params | num_ctx 64k VRAM est. |
|-------|--------|-----------------------|
| qwen2.5-coder:7b | 7B | ~8-10 GB |
| qwen2.5-coder:14b | 14B | ~14-18 GB |
| llama3.1:8b | 8B | ~9-11 GB |
| llama3.1:70b (Q4) | 70B | Won't fit with 64k ctx |
| deepseek-coder-v2:16b | 16B | ~16-20 GB |

With 24GB VRAM, 7B-14B models at 64k context are feasible. 70B models need 32k or lower.

### Action Required

Add to `README.md` and/or a `.env.example`:
```
# MANDATORY: Set context window before running factory
# Default 4096 is insufficient. Minimum 64k required.
OLLAMA_CONTEXT_LENGTH=65536
```

Or add `num_ctx` to LLMClient API calls if using Ollama's native format.

---

## Architecture Overview

```
vibe.md  -->  Foreman (plan)  -->  specs/specs.md + scenarios/scenarios.md
                                        |
                                        v
                                 Worker (build)
                                   |-- Professor (skills)
                                   |-- Plumber (backend)       } parallel by
                                   |-- Sculptor (frontend)     } dependency level
                                   |-- Registrar (infra)       }
                                   |-- ... 8 more specialists  }
                                   |-- Generalist (catch-all)
                                   |-- Deep-Crawl (missing imports)
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

1. **Economic split** -- Expensive model plans once, cheap model codes N times. Core thesis is correct.
2. **Specialist Council** -- 12 domain specialists with topological dependency ordering and parallel execution via `asyncio.gather`. Battle-tested anti-gaslighting prompts and runt prevention.
3. **Deep-Crawl** -- Recursive scanning of generated App.tsx for imports referencing ungenerated files. Addresses a real and common LLM code-gen failure mode.
4. **Feedback loop** -- `questionnaire.py` appends to `vibe.md`, `critique.md` feeds back to Foreman. Iterative convergence.
5. **Playwright verification** -- Judge now boots the app via RunManifest, runs headless Chromium, checks page load/title/UI markers, feeds report into verdict.
6. **DarkLogger** -- Proper `logging.getLogger` with `RotatingFileHandler` (5MB, 5 backups), Rich console handler, tail/export utilities.
7. **Context Hardening** -- Specialists receive up to 50k chars of spec context, resolving the earlier contradiction between anti-gaslighting demands and truncated specs.
8. **Async throughout** -- `AsyncOpenAI`, all specialist generates are `async`, parallel level execution.

---

## Known Issues (Ordered by Severity)

### ~~BLOCKER: Generalist.requires Is Broken~~ FIXED (2026-02-08)

Generalist requires reverted to plain strings. Dependency resolver in `worker.py` also hardened with `_resolve_req_name()` to handle string or dict requires defensively.

### HIGH: DTU Not Connected

`dtu/main.py` has 3 hardcoded endpoints (Stripe mock, auth mock, health). Nothing in the pipeline connects the generated app to DTU:
- No env vars injected into generated code
- No proxy configuration in vite.config pointing at DTU
- `factory.py` spins up DTU but judge's RunManifest doesn't know about it
- Generated apps have zero awareness of DTU's existence

### HIGH: RunManifest Default Layout Mismatch

`run_manifest.py` defaults to `npm start` in `server/` and `client/` subdirectories. But the factory generates flat structures (package.json and server.js at output root). If no manifest.json exists in the output, `boot()` will fail because `output_XXX/server/` doesn't exist.

### MEDIUM: factory.py Not Modernized

`factory.py` still uses raw `console.print()` throughout -- no DarkLogger, no GitManager, no RunManifest. It's the only file that wasn't updated in the logging migration. It also invokes worker.py and judge.py via `subprocess.run()`, which means:
- Token usage from worker and judge LLMClient instances is lost (separate processes)
- No aggregated cost reporting possible
- No shared state between orchestrator and components

### MEDIUM: GitManager Exists But Is Unwired

`src/utils/git_manager.py` has `initialize()` and `commit_changes()` but nothing in the pipeline calls it. Generated output directories have no git history.

### MEDIUM: Token Usage Never Reported

`LLMClient.get_usage()` exists with `tokens_used = {"input": 0, "output": 0}` but is never called. The PRD's core thesis is cost efficiency, but there is no measurement or reporting of token consumption.

### ~~LOW: LLMClient Still Uses console.print for Errors~~ FIXED (2026-02-08)

LLMClient migrated to `logging.getLogger("dark_factory")`. Added context window overflow warning, per-call debug logging of token counts, `get_usage_summary()` method, and proper structured error messages.

### LOW: foreman.py Import Path Inconsistency

`foreman.py` uses `from utils.logger import logger` (relies on sys.path.append to src/) while `worker.py` uses `from src.specialists.council import ...` (uses src. prefix). Inconsistent import conventions.

### DEFERRED: Kitchen-Sink Dependencies

The Registrar hardcodes 35+ npm dependency groups (Three.js, Tone.js, MIDI, epub-parser, WhatsApp, Telegram, etc.) for every generated app regardless of the vibe. This is acceptable during development for maximum capability coverage. Must be whittled down to vibe-relevant deps before any public release.

---

## Improvement Roadmap

### Phase 1: Fix Blockers (Now)

- [ ] Fix Generalist.requires dict/string mismatch
- [ ] Fix RunManifest default layout to match flat structure
- [ ] Add `OLLAMA_CONTEXT_LENGTH=65536` to README and .env.example
- [ ] Wire GitManager into factory pipeline (init after build, commit after judge pass)

### Phase 2: Complete the Pipeline (Next)

- [ ] Migrate factory.py to DarkLogger
- [ ] Wire DTU to generated apps (env vars, proxy config)
- [ ] Report token usage at end of factory run
- [ ] Migrate LLMClient error logging to DarkLogger
- [ ] Add run metadata JSON per output (model, vibe hash, timestamp, tokens, verdict)

### Phase 3: Production Hardening

- [ ] Guard against context window overflow (measure prompt size vs model limit)
- [ ] Dynamic dependency selection (analyze specs to determine needed npm packages)
- [ ] Normalize import paths (decide on `src.` prefix or sys.path.append, not both)
- [ ] Cross-platform support (kill_zombies is Windows-only)

### Phase 4: meta-mcp Integration

- [ ] Expose factory phases as meta-mcp agents (see docs/META_MCP_INTEGRATION.md)
- [ ] Agent lifecycle: start/poll/await for Foreman, Worker, Judge
- [ ] Swarm mode: multiple Workers in parallel on different features

---

## Round-by-Round Progress

| Issue | R1 | R2 | R3 |
|-------|----|----|-----|
| Async LLM | Blocking | AsyncOpenAI | AsyncOpenAI |
| Parallel specialists | Sequential | asyncio.gather | asyncio.gather |
| Token tracking | None | Tracked, not reported | Tracked, not reported |
| Judge executes app | Hardcoded fake | Real file list | **Playwright + RunManifest** |
| Structured logging | None | None | **DarkLogger + rotation** |
| .gitignore | Missing | Missing | **Comprehensive** |
| Git integration | None | None | **Class exists, unwired** |
| Help system | None | None | **HelpOracle (4 levels)** |
| Context window | 1.5-2k chars | 1.5-2k chars | **50k chars** |
| Architecture doc | None | None | **ARCHITECTURE.md** |
| DTU connected | No | No | No |
| Kitchen-sink deps | Yes | Yes | Yes (deferred) |
| Generalist requires | Works | Works | **BROKEN** |
| factory.py logging | console.print | console.print | console.print |

---

## File Inventory

```
dark-app-factory/
  factory.py           # Orchestrator (needs modernization)
  foreman.py           # Planner (logging migrated)
  worker.py            # Execution engine (async, parallel, logging)
  judge.py             # Quality gate (Playwright, RunManifest, logging)
  run_manifest.py      # Process orchestrator for generated apps
  questionnaire.py     # Human feedback loop
  vibe.md              # User intent input
  PRD.md               # Product requirements
  .gitignore           # Comprehensive
  pyproject.toml       # Hatchling build system
  requirements.txt     # Python deps
  src/
    llm_client.py      # AsyncOpenAI with token tracking
    auditor.py         # Playwright-based runtime auditor
    specialists/
      base.py          # Abstract Specialist class
      council.py       # 12 specialist implementations
    utils/
      logger.py        # DarkLogger singleton
      help_oracle.py   # Tiered help system
      git_manager.py   # Git init/commit (unwired)
  dtu/
    main.py            # Digital Twin Universe (skeleton)
  docs/
    ARCHITECTURE.md    # System architecture doc
    META_MCP_INTEGRATION.md  # meta-mcp cross-utilization plan
  specs/               # Generated specs and research
  scenarios/           # Generated test scenarios
  skills/              # Domain knowledge files
  outputs/             # Generated app directories
```
