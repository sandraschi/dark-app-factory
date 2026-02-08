# Dark App Factory Architecture

Dark App Factory is an industrial-grade, parallelized generative engine designed to produce SOTA (State of the Art) web applications from high-level "vibes".

## 1. Core Philosophy
- **Anti-Gaslighting**: The system uses rigorous verification (The Satisficer) to ensure generated code matches observed technical reality.
- **Materialist/Reductionist**: Code is treated as empirical data. Design is driven by functional requirements first, aesthetics second.
- **High-Fidelity**: No skeletons. No placeholders. Every file is generated as production-ready logic.

## 2. Component Hierarchy

### Foreman (`foreman.py`)
- **Role**: Architect & Planner.
- **Logic**: Converts user intent (vibe.md) into technical specifications (specs.md) and QA scenarios (scenarios.md).
- **Oracle**: Leverages search data to ensure 2026-standard compliance.

### Worker (`worker.py`)
- **Role**: Execution Engine.
- **Specialist Council**: Orchestrates 12+ domain-specific AI Specialists.
- **Parallel Pipeline**: Executes specialist tasks in dependency-aware levels (e.g., Plumber -> Librarian).
- **Deep-Crawl**: Recursively scans generated code to find and implement missing components.

### Satisficer (`judge.py`)
- **Role**: Quality Gate.
- **Verification**: Performs physical file checks and logical audits using the `Auditor` specialist.
- **Verdict**: Issues a PASS/FAIL verdict. On failure, generates a `critique.md` for the Foreman to fix.

## 3. Specialist Council
The Council is a set of modular AI roles defined in `src/specialists/council.py`:

| Specialist | Domain | Responsibility |
| :--- | :--- | :--- |
| **Plumber** | Backend | API architecture, Node.js, Express, SQL, Auth. |
| **Sculptor** | Frontend | React, Three.js, Glassmorphism, Generative UI. |
| **Librarian** | Docs | README.md and technical documentation. |
| **Professor** | Skills | Domain-specific skill battery injection. |
| **Nervos** | System | Heartbeat, Messaging (WhatsApp/Telegram), Plugins. |
| **Raggy** | RAG | Embeddings, Vector Search, Semantic Search. |
| **Maestro** | Audio | Generative Music, Web Audio, Tone.js. |
| **Auditor** | Finance/QA | Excel/Word parsing, Data validation, "Cook my books". |

## 4. Reliability Enhancements (v1.1)
- **Context Hardening**: All specialists now receive up to 50,000 characters of specification context to prevent missing requirements.
- **Structured Logging**: Unified logging system (`DarkLogger`) ensures all operations are persistent, auditable, and human-readable.
- **Anti-Runt Logic**: Automatic detection and retry for implementations that are too short/skeletal.
