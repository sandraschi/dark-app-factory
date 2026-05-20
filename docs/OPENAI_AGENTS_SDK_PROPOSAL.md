---
title: "Proposal: OpenAI Agents SDK as Dark App Factory v2.0 Orchestration Layer"
category: architecture
status: proposal
related:
  - ARCHITECTURE.md
  - ../PRD.md
  - STRONGDM_ANALYSIS.md
last_updated: 2026-04-24
author: Sandra Schi
---

# Proposal: OpenAI Agents SDK as Dark App Factory v2.0 Orchestration Layer

**Status:** Proposal — v2.0 candidate  
**Priority:** Aligns with v2.0 roadmap item: "Multi-agent recursive self-healing"  
**Effort estimate:** 1 week PoC; 2–3 weeks for full Specialist Council migration  
**Repo:** [openai/openai-agents-python](https://github.com/openai/openai-agents-python) — MIT, provider-agnostic, native MCP client  

---

## 1. Executive Summary

Dark App Factory already implements a multi-agent pipeline: Foreman → Specialist Council (19 agents, tiered) → Judge. This is driven by a hand-rolled `asyncio.gather` orchestrator in `worker.py`, with manual LLM calls via `LLMClient`, retry loops in `base.py`, and validation hooks per specialist.

The OpenAI Agents SDK is a direct fit for replacing this infrastructure. The Specialist Council becomes a set of `Agent` objects with dependency-resolved handoffs. The Judge becomes an `OutputGuardrail` or a dedicated Agent with Playwright tool access. The Foreman → Worker → Judge phase sequence becomes typed handoffs with automatic runner loop management.

The net effect on v2.0's stated goal — "multi-agent recursive self-healing" — is that the SDK provides the retry/correction loop for free via its max-turns runner and handoff-back-to-foreman patterns, rather than requiring a bespoke recursive implementation.

The economics argument (core to the PRD) is preserved: Foreman uses Claude Sonnet via the Anthropic API, Workers use local Qwen3.5 27B via Ollama's OpenAI-compat endpoint. The SDK supports mixed providers per agent natively.

---

## 2. Background: Current Implementation

The pipeline is spread across:

```
foreman.py          # Enrich + Plan (LLM calls via LLMClient)
worker.py           # Specialist Council orchestrator (asyncio.gather tiers)
factory.py          # Full pipeline: Research → Plan → DTU → Build → Landing → Judge → Launch
judge.py            # Playwright-based quality gate
src/specialists/
  base.py           # Base class: validate(), declare_files(), get_dependency_context()
  council.py        # All 19 Specialist definitions
dtu/main.py         # Digital Twin Universe (mock external APIs)
run_manifest.py     # Boot generated app with DTU env vars injected
```

The current orchestration model in `worker.py`:

```python
# Tier-resolved parallel execution (current)
tier_groups = resolve_dependency_tiers(specialists)
for tier in tier_groups:
    await asyncio.gather(*[
        specialist.generate(file, specs, shared_context)
        for file in tier_files
    ])
```

Validation on failure injects error messages into a retry prompt — up to 3 retries per specialist, with no coordination between specialists on failure. The Judge is a separate post-build step with no feedback loop back into the specialist pipeline.

The v2.0 roadmap entry explicitly calls for replacing this with "multi-agent recursive self-healing" and a "meta-mcp agent lifecycle."

---

## 3. How the SDK Maps to Dark App Factory

### 3.1 Foreman as Planner Agent

```python
from agents import Agent, OpenAIChatCompletionsModel
from openai import AsyncOpenAI

# Foreman: high-intelligence, used sparingly (< 1% of tokens per PRD)
claude_client = AsyncOpenAI(
    base_url="https://api.anthropic.com/v1",
    api_key=ANTHROPIC_API_KEY
)

foreman = Agent(
    name="Foreman",
    model=OpenAIChatCompletionsModel(
        model="claude-sonnet-4-6",  # or local Llama 3.1 for offline mode
        openai_client=claude_client
    ),
    instructions=FOREMAN_SYSTEM_PROMPT,
    handoffs=[handoff(worker_council, tool_name_override="dispatch_to_workers")]
)
```

When the Foreman's plan is complete, it calls `dispatch_to_workers` and the SDK runner transitions control automatically.

### 3.2 Specialist Council as Agent Pool with Parallel Handoffs

The current tier-based `asyncio.gather` maps to parallel handoffs. The SDK supports parallel tool calls within a single agent turn — Specialists that share a tier can be dispatched simultaneously:

```python
# Each Specialist becomes an Agent
plumber = Agent(
    name="Plumber",
    model=ollama_qwen,  # local, cheap
    instructions=PLUMBER_SYSTEM_PROMPT,
    tools=[write_file_tool, read_specs_tool]
)

sculptor = Agent(
    name="Sculptor",
    model=ollama_qwen,
    instructions=SCULPTOR_SYSTEM_PROMPT,
    tools=[write_file_tool, read_dependency_context_tool]
)

# Worker Council Agent orchestrates the specialist pool
worker_council = Agent(
    name="WorkerCouncil",
    model=ollama_qwen,
    instructions=WORKER_COUNCIL_PROMPT,
    handoffs=[
        handoff(plumber),
        handoff(sculptor),
        handoff(registrar),
        # ... all 19 specialists
    ]
)
```

The Worker Council agent decides which specialists to dispatch and in what order, driven by the spec's dependency declarations — replacing the static tier resolution in `worker.py`.

### 3.3 Judge as OutputGuardrail + Agent

The Judge currently runs as a separate post-build step. With the SDK, it can be wired as both a guardrail (blocking output before it's considered "done") and an autonomous agent that can request rework:

```python
from agents import output_guardrail, GuardrailFunctionOutput

@output_guardrail
async def judge_guardrail(ctx, agent, output) -> GuardrailFunctionOutput:
    """Run Playwright audit on generated output. Fail if PASS threshold not met."""
    verdict = await run_playwright_audit(output.generated_path)
    if verdict.score < PASS_THRESHOLD:
        # Inject critique back into context for rework
        return GuardrailFunctionOutput(
            output_info={"critique": verdict.critique_md, "failures": verdict.failures},
            tripwire_triggered=True  # blocks completion, triggers rework loop
        )
    return GuardrailFunctionOutput(tripwire_triggered=False)

worker_council = Agent(
    name="WorkerCouncil",
    output_guardrails=[judge_guardrail],
    max_turns=5  # caps recursive rework attempts
)
```

When the guardrail fires, the SDK feeds the `critique_md` back into the agent context and the Worker Council re-dispatches affected Specialists. This is the "recursive self-healing" v2.0 goal — implemented without bespoke recursive logic.

### 3.4 Dependency Context as Agent Context Variables

Currently `base.py`'s `get_dependency_context()` pulls output from `requires` specialists and injects it into prompts (capped at 8,000 chars). The SDK has a `RunContextWrapper` that persists across the entire run — this becomes the shared context store:

```python
from agents import RunContextWrapper
from dataclasses import dataclass

@dataclass
class FactoryRunContext:
    specs: str
    stack_profile: dict
    shared_outputs: dict[str, str]  # specialist_name -> generated content
    dtu_url: str

# Downstream specialists read from ctx.context.shared_outputs
async def plumber_tool(ctx: RunContextWrapper[FactoryRunContext], ...):
    professor_output = ctx.context.shared_outputs.get("Professor", "")
    # inject into prompt...
```

This replaces the `shared_context` dict threading through `worker.py` with a typed, SDK-managed context object accessible to all agents in the run.

### 3.5 Self-Healing Loop (v2.0 Goal)

The current retry logic in `base.py` is per-specialist and limited to 3 retries with error injection. It has no awareness of what other specialists produced. With the SDK:

```
Foreman plans → WorkerCouncil dispatches specialists in tiers
                     ↓
              Specialists produce files
                     ↓
              Judge guardrail fires (FAIL + critique)
                     ↓
              SDK feeds critique into WorkerCouncil context
                     ↓
              WorkerCouncil re-dispatches only failing specialists
              (with critique + other specialists' outputs as context)
                     ↓
              Judge guardrail re-runs
                     ↓ (max_turns exhausted)
              Adjudicator synthesizes best partial output + critique.md
```

This is multi-agent recursive self-healing. The SDK runner handles the loop; `max_turns` prevents infinite recursion. The critique propagation is automatic via context.

---

## 4. Economics Preservation

The PRD's token economy (< 1% high-intelligence tokens) is preserved:

| Agent | Model | Token Role |
|---|---|---|
| Foreman | Claude Sonnet / Llama 3.1 | Planning only — called once per run |
| WorkerCouncil | Qwen3.5 27B Q4 (Ollama) | Dispatch decisions — cheap |
| Each Specialist (19) | Qwen3.5 27B Q4 (Ollama) | All code generation — bulk of tokens, local |
| Judge | Qwen3.5 27B Q4 (Ollama) + Playwright | Verification — local |
| Adjudicator (new) | Claude Sonnet | Final synthesis on failure — called rarely |

The SDK's `model=` is per-Agent, not global. No architectural change needed to maintain the hybrid economy.

---

## 5. What Replaces What

| Current Component | SDK Replacement | Notes |
|---|---|---|
| `worker.py` tier orchestrator | `Agent` handoffs + `Runner.run()` | Dynamic dispatch replaces static tier resolution |
| `base.py` validate() + retry loop | `OutputGuardrail` + `max_turns` | System-managed, not per-specialist |
| `base.py` get_dependency_context() | `RunContextWrapper` shared context | Typed, accessible to all agents |
| `LLMClient` per-call wrapper | `Agent(model=...)` per agent | Per-agent model config |
| `judge.py` post-build step | Guardrail + Judge Agent with critique feedback | Integrated into the loop, not a separate step |
| `shared_context` dict in worker.py | `FactoryRunContext` dataclass | Typed, SDK-managed |

**Unchanged:**
- `foreman.py` enrich/plan logic (prompts move to Agent `instructions`)
- `dtu/main.py` Digital Twin Universe — still starts before the build, DTU URL injected via `FactoryRunContext.dtu_url`
- `run_manifest.py` — unchanged, called by the Judge agent or its tools
- All Specialist prompt content from `council.py`
- Dashboard + progress API (SDK tracing feeds the progress layer)
- `stack_profile.py`, `git_manager.py`, `help_oracle.py`
- All output directory structure

---

## 6. Migration Plan

### Phase A — PoC: Single Specialist via SDK (3–4 days)

1. `uv add openai-agents` to `pyproject.toml`
2. Port one Specialist (Plumber — most deterministic) to an `Agent` with `write_file` as a tool
3. Port Foreman → Plumber as a handoff
4. Port `base.py` validate() as an `OutputGuardrail` on the Plumber agent
5. Verify output parity with current system on a known vibe

### Phase B — Full Specialist Council (1.5 weeks)

1. Port all 19 Specialists to Agent objects (prompts from `council.py`, verbatim)
2. Implement `FactoryRunContext` as the shared context type
3. Implement tier-aware `WorkerCouncil` orchestrator agent
4. Port `get_dependency_context()` to context reads
5. Wire `judge.py` Playwright logic as an `OutputGuardrail`
6. Implement `max_turns=5` rework loop

### Phase C — Self-Healing + Dashboard Integration (1 week)

1. Implement `RobofangStyleTraceProcessor` → feeds SDK trace events to `/api/progress` endpoint
2. Implement Adjudicator agent for final synthesis on max_turns exhaustion
3. Port `factory.py` pipeline steps to SDK `Runner.run()` with the Foreman as entry point
4. Update dashboard to consume SDK trace events (specialist status: PENDING/RUNNING/DONE/FAILED)

---

## 7. Risks

| Risk | Likelihood | Mitigation |
|---|---|---|
| Parallel specialist dispatch latency with local Ollama (19 simultaneous calls) | Medium | SDK supports parallel tool calls but Ollama queues requests; benchmark with current parallel baseline before committing |
| WorkerCouncil agent making suboptimal dispatch decisions vs static tier resolution | Medium | Fallback: keep static tier resolution as a tool the WorkerCouncil can call; SDK agent is advisory, tiers are the floor |
| Judge guardrail tripwire causing runaway rework loops on edge-case apps | Low | `max_turns=5` hard cap; exponential backoff between rework attempts |
| SDK context window limits on large specs (50k chars currently injected) | Low | Specs stay in `FactoryRunContext` object, not in the prompt window; agents read via tool calls |

---

## 8. Relationship to RoboFang Proposal

The [RoboFang SDK proposal](../../robofang/docs/architecture/OPENAI_AGENTS_SDK_PROPOSAL.md) targets the same SDK for a different use case: Council-of-Dozens orchestration over a live MCP fleet. Dark App Factory's use case is simpler in one dimension (no physical actuation, no trust tiers) and more complex in another (19 parallel specialists, self-healing rework loop, Playwright verification).

The two proposals are independent — adopting the SDK in one repo does not depend on the other. However, lessons from the RoboFang PoC (particularly Ollama tool-call reliability) directly inform Phase A here.

---

## 9. Dependency Addition

```toml
# pyproject.toml addition
[project.dependencies]
# existing...
openai-agents = ">=0.0.10"
```

No conflict with current FastAPI / Playwright / Ollama stack.

---

## 10. Related Documents

- [ARCHITECTURE.md](ARCHITECTURE.md) — current pipeline design; SDK replaces §3 Worker orchestration and §6 Judge integration
- [PRD.md](../PRD.md) — v2.0 goal: "Multi-agent recursive self-healing"
- [STRONGDM_ANALYSIS.md](STRONGDM_ANALYSIS.md) — Pyramid Summaries and multi-agent techniques; SDK enables several of these
- [openai-agents-python](https://github.com/openai/openai-agents-python) — upstream SDK
- [RoboFang SDK Proposal](../../robofang/docs/architecture/OPENAI_AGENTS_SDK_PROPOSAL.md) — parallel adoption in the fleet orchestration context
