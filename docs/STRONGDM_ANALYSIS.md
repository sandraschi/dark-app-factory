# StrongDM Factory: Analysis & Inspiration

**Source**: [factory.strongdm.ai](https://factory.strongdm.ai)
**Analysis Date**: 2026-02-08
**Dark App Factory**: Local-first, low-cost implementation inspired by this methodology.

---

## TL;DR

StrongDM built a **Software Factory** where specs + scenarios drive agents that write code and converge without human review. Their approach is correct and compelling. Their economics are not: they explicitly target **$1,000 per developer per day** in API tokens. Dark App Factory replicates the methodology for **free** using Ollama and local models.

---

## The $1,000 Quote

> "If you haven't spent at least **$1,000 on tokens today** per human engineer, your software factory has room for improvement."
> — StrongDM Factory, [factory.strongdm.ai](https://factory.strongdm.ai)

This is their stated benchmark. For a team of 10 engineers, that's $10,000/day, $50,000/week, $200,000+/month — in API costs alone.

Our reaction: *spit out the coffee, then think: we can do this for free.*

---

## What StrongDM Factory Is

### Core Definition

A **Software Factory** is non-interactive development where:

1. **Specs + Scenarios** drive the process (not human-written code)
2. **Agents** write code, run harnesses, and converge
3. **No human review** — code must not be written or reviewed by humans
4. **Validation** is empirical (externally observable behavior), not semantic (reading source)

### Their Rules (Kōan Form)

- *Why am I doing this?* (implied: the model should be doing this instead)
- **Code must not be written by humans**
- **Code must not be reviewed by humans**

### The Loop

1. **Seed** — PRD, spec, few sentences, screenshot, or existing codebase
2. **Validation** — End-to-end harness, as close to real environment as possible
3. **Feedback** — Sample of output fed back into inputs. Closed loop until holdout scenarios pass.

### Key Concepts We Adopted

| StrongDM Term | Our Equivalent | Notes |
|---------------|----------------|-------|
| **Seed** | `vibe.md` + `foreman plan` | Our Foreman expands vibe into specs |
| **Scenarios** | `scenarios/scenarios.md` | End-to-end user stories, LLM-validated |
| **Satisfaction** | Satisficer (Judge) | Probabilistic/empirical verdict |
| **Digital Twin Universe (DTU)** | `dtu/main.py` | Behavioral clones of external APIs |
| **Validation harness** | Playwright + RunManifest | Boot app, run scenarios, LLM verdict |

### Their Digital Twin Universe

StrongDM built behavioral clones of:

- Okta (auth)
- Jira (ticketing)
- Google Docs
- Google Drive
- Google Sheets
- Slack

Purpose: Validate at volumes and rates far exceeding production limits. No rate limits, no API costs, no abuse detection. Thousands of scenarios per hour.

**Our DTU**: Stripe, Auth, Email, SMS, Storage, Discord, Slack, Weather, generic webhook. Same idea, smaller surface area, fully local.

---

## Their Techniques (We Implemented a Subset)

| Technique | StrongDM | Dark App Factory |
|-----------|----------|------------------|
| **DTU** | Okta, Jira, Docs, Drive, Sheets, Slack | Stripe, Auth, Email, SMS, Storage, Discord, Slack, Weather |
| **Gene Transfusion** | Point agents at exemplars | `skills/` battery, Professor specialist |
| **Filesystem** | Models navigate repos, read/write | Worker writes to output dir, Deep-Crawl scans imports |
| **Shift Work** | Specs complete → agent runs E2E | `foreman plan` → `worker build` → `judge` pipeline |
| **Pyramid Summaries** | Reversible multi-level compression | Not implemented |
| **Semport** | Semantic porting between languages | Multi-stack (Python/Node, React/HTMX) via stack profile |

---

## The Validation Constraint

StrongDM's constraint (given zero hand-written code, zero traditional review):

1. **Grow from cascades of natural-language specifications**
2. **Be validated automatically without semantic inspection of source**

Code is treated like an ML model snapshot: **opaque weights** whose correctness is inferred **exclusively from externally observable behavior**. Internal structure is opaque.

We follow this. Our Judge uses Playwright (observable UI/API) and an LLM verdict. We do not semantically inspect generated Python/TSX for "correctness" — we run it and check if it satisfies scenarios.

---

## Economics: The Main Divergence

| Dimension | StrongDM | Dark App Factory |
|-----------|----------|------------------|
| **Token budget** | $1,000+/dev/day target | ~$0 (Ollama local) |
| **Models** | Claude, frontier cloud APIs | qwen2.5-coder, deepseek-coder, llama (local) |
| **Planning** | Presumably frontier models | Foreman: Opus or local (configurable) |
| **Coding** | Frontier models, high volume | Workers: local models only |
| **Validation** | LLM-as-judge, scenarios | Same pattern, local or cheap model |
| **DTU** | Custom clones of Okta, Jira, etc. | Generic mocks (Stripe, Auth, etc.) |

**Our thesis**: The methodology (specs → scenarios → agents → validation) is model-agnostic. The economic model (spend $1k/day) is optional. We can run the same loop on local hardware with zero marginal cost per run.

---

## References They Cite

- Luke PM — ["The Software Factory"](https://lukepm.com/blog/the-software-factory/)
- Sam Schillace — ["I Have Seen the Compounding Teams"](https://sundaylettersfromsam.substack.com/p/i-have-seen-the-compounding-teams)
- Dan Shapiro — ["Five Levels from Spicy Autocomplete to the Software Factory"](https://www.danshapiro.com/blog/2026/01/the-five-levels-from-spicy-autocomplete-to-the-software-factory/)
- Other factories: Devin, 8090, Factory (Matan Grinberg), Superconductor, Superpowers (Jesse Vincent)

---

## What We Left Out (For Now)

1. **Pyramid Summaries** — Reversible summarization at multiple zoom levels (inspired by Pyramid TIFF, map tiles). E.g. "Summarize this bug report in 2 words. Now 4. Now 8. Now 16." Each level preserves meaning while expanding/contracting detail. Agents can survey hundreds of items at 2-word level, identify interesting ones, expand only those. Combines with MapReduce + Clustering: Map (generate pyramid summaries in parallel) -> Cluster (group by compressed reps) -> Reduce (synthesize, expand where needed). Context windows are finite; this lets you see forest and trees, not all at once. We use flat 50k char injection instead.
2. **Semport** — Semantic porting between langs/frameworks. We have multi-stack generation but not automated migration.
3. **Enterprise DTU targets** — Okta, Jira, Google Workspace. Our DTU is generic (auth, payments, storage, webhooks). Could extend.
4. **Synthetic scenario curation UI** — StrongDM has a "shaping interface" for scenarios. We have `scenarios/scenarios.md` as plain text.

---

## Summary

StrongDM Factory validated the core methodology: specs + scenarios → agents → validation harness → feedback loop. Their Digital Twin Universe, shift work, and validation constraint are sound. Their economics ($1k/dev/day) are a non-starter for vibecoders and indie teams.

Dark App Factory is the same methodology, run on local models, for free.
