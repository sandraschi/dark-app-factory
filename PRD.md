# Dark App Factory: The "Lights Out" Dev Scaffold for Vibecoders

> **Mission**: Democratize "Software Factory" methodology for the vibecoder community using low-cost/local models (Ollama/DeepSeek) with strategic injection of high-intelligence compute (Opus 4.6).

## Abstract
The **Dark App Factory** is an open-source scaffold and workflow engine designed to replicate the "Factory" methodology (Specs + Scenarios -> Agents -> Code) without the enterprise price tag. It decouples **Intelligence (Planning)** from **Labor (Coding)** to optimize for cost and speed.

## Core Philosophy
1.  **Find Knobs, Turn to Eleven**: If testing is good, 1000 tests are better. If mocks are good, full Digital Twins are better.
2.  **Unconventional Economics**: Use "smart" models (Opus 4.6) *only* for architectural/spec definition (< 1% of tokens). Use "dark" models (Ollama/DeepSeek/Qwen) for implementation loops (> 99% of tokens).
3.  **Physical Grounding**: Real-world file-system audits and logical verification replace hallucinated test results.
4.  **Distribution by Default**: Every app gets a marketing kit and landing page, not just code.

## Architecture v1.3

### 1. The Enricher (New in v1.3)
*   **Command**: `foreman enrich`
*   **Role**: LLM-augmented expansion of terse vibes into rich domain briefs.
*   **Output**: `enriched_vibe.md` for user review before planning.

### 2. The Foreman (Intelligence Layer)
*   **Model**: Opus 4.6 / Llama 3.1 (configurable).
*   **Role**: Generates the **Blueprint** (`specs.md`, `scenarios.md`) with embedded stack profile.

### 3. The Factory Floor (Labor Layer)
*   **Engine**: **Async-Parallel Orchestrator** with dependency-resolved tiers.
*   **Workers**: 18 Specialized agents + Generalist catch-all.
*   **Sophistication Features**:
    -   **Context Injection**: Downstream specialists read upstream output.
    -   **Validation Hooks**: Domain-specific quality gates with retry.
    -   **Self-Declaration**: Specialists inject files they need based on specs keywords.
    -   **Temperature Tuning**: Precision (0.1) to creative (0.7) per specialist.
    -   **Multi-Stack**: Python/Node backend, React/HTMX/none frontend.

### 4. The Propagandist (Distribution Layer, New in v1.3)
*   **Role**: Generates marketing/distribution assets for every build.
*   **Council Member**: Shakespeare writes copy, Propagandist formats for platforms.
*   **Output**: Press release, blog, social media kit, email pitches, Reddit/Discord/PH posts, landing page HTML.
*   **Factory Step**: Auto-generates `www/index.html` landing page.

### 5. The Digital Twin Universe (DTU)
*   **Role**: Provides local clones of external APIs (Stripe, Discord, etc.) for non-blocking integration testing.

### 6. The Satisficer (SOTA Judge)
*   **Role**: Performs **Empirical Verification**.
*   **Audit**: Live UI/API audits using **Playwright**.
*   **Verdict**: PASS/FAIL with `critique.md` feedback loop.

### 7. The Help Oracle & Logging
*   **Role**: On-demand documentation and log diagnostic layer.
*   **Leveling**: Basic to Expert help system.
*   **Diagnostics**: DarkLogger with rotation and export.

## Workflow: The "Dark Logic"

```
1. vibe.md          -- User defines intent + tech stack
2. foreman enrich   -- LLM expands vibe (user reviews)
3. foreman plan     -- Specs + scenarios generated
4. factory run      -- Full pipeline:
   a. Research (Oracle)
   b. Plan (Foreman)
   c. Build (Worker Council, parallel)
   d. Distribute (Propagandist, landing page)
   e. Mock (DTU)
   f. Judge (Satisficer, Playwright)
   g. Launch + Audit
```

## Roadmap Status
- [x] **v0.1-v0.4**: Prototype development.
- [x] **v1.0**: Architectural Hardening (Async Parallelism).
- [x] **v1.1**: System Surge (Playwright Judging, Help Oracle, Logging, Git).
- [x] **v1.2**: Multi-Stack Factory (Python/Node, React/HTMX).
- [x] **v1.3 (Current)**: Council Sophistication + Vibe Enrichment + Marketing Pipeline.
- [ ] **v1.4**: Wire DTU to generated apps. Token usage reporting. GitManager integration.
- [ ] **v2.0**: Multi-agent recursive self-healing. meta-mcp agent lifecycle.
