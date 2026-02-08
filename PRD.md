# Dark App Factory: The "Lights Out" Dev Scaffold for Vibecoders

> [!IMPORTANT]
> **Mission**: Democratize "Software Factory" methodology for the vibecoder community using low-cost/local models (Ollama/DeepSeek) with strategic injection of high-intelligence compute (Opus 4.6).

## Abstract
The **Dark App Factory** is an open-source scaffold and workflow engine designed to replicate the "Factory" methodology (Specs + Scenarios -> Agents -> Code) without the enterprise price tag. It decouples **Intelligence (Planning)** from **Labor (Coding)** to optimize for cost and speed.

## Core Philosophy
1.  **Find Knobs, Turn to Eleven**: If testing is good, 1000 tests are better. If mocks are good, full Digital Twins are better.
2.  **Unconventional Economics**: Use "smart" models (Opus 4.6) *only* for architectural/spec definition (< 1% of tokens). Use "dark" models (Ollama/DeepSeek/Qwen) for implementation loops (> 99% of tokens).
3.  **Physical Grounding**: Real-world file-system audits and logical verification replace hallucinated test results.

## Architecture v1.0 (SOTA)

### 1. The Foreman (Intelligence Layer)
*   **Model**: Opus 4.6 (SOTA).
*   **Role**: Generates the **Blueprint** (`specs.md`, `scenarios.md`).

### 2. The Factory Floor (Labor Layer)
*   **Engine**: **Async-Parallel Orchestrator**.
*   **Workers**: Specialized agents (Plumber, Sculptor, Maestro, etc.).
*   **Execution**: Dependency-aware parallel processing (Levels 1-4).

### 3. The Digital Twin Universe (DTU)
*   **Role**: Provides local clones of external APIs (Stripe, Discord, etc.) for non-blocking integration testing.

### 4. The Satisficer (SOTA Judge)
*   **Role**: Performs **Empirical Verification**.
*   **Audit**: Scans file-system for physical presence, cross-references API routes, and performs logical audits.
*   **Verdict**: SOTA physical/logical pass.

## Workflow: The "Dark Logic"

1.  **Vibe Check**: User defines `vibe.md`.
2.  **Blueprint**: `foreman.py plan` generates specs.
3.  **Build**: `worker.py build` triggers the parallel specialist council.
4.  **Audit**: `judge.py judge` conducts a non-fictional QA gauntlet.

## Roadmap Status
- [x] **v0.1-v0.4**: Prototype development.
- [x] **v1.0 (Current)**: SOTA Architectural Hardening (Async Parallelism, Real-World Judging).
- [ ] **v1.1**: Expanded DTU targets (Twitter, AWS, Slack).
- [ ] **v2.0**: Multi-agent recursive self-healing.
