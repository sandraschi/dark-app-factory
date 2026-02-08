# Dark App Factory 🏭🌑

**"Software Factories for the Rest of Us."**

A local-first, low-cost implementation of the "Software Factory" methodology (Spec -> Scenarios -> Agent Loop).
Designed for Vibecoders who want enterprise-grade autonomous development without the enterprise-grade bill using Ollama, DeepSeek, and other local models.

## 🏗️ Architecture v1.0 (SOTA)

The factory floor is now powered by an **Async-Parallel Orchestrator** and a **Council of Specialists**.
For a deep dive into the specialist roles and system design, see [ARCHITECTURE.md](file:///d:/dev/repos/dark-app-factory/docs/ARCHITECTURE.md).

- **Foreman** 🧠: High-intelligence Planner (Opus/Claude 3.5 Sonnet) -> Generates Strict Specs (Architecture, SQL, API).
- **The Specialist Council** 👷: 10+ niche agents (Plumber, Sculptor, Librarian, etc.) executing in parallel based on a dependency graph.
- **Async Orchestrator** ⚡: Refactored logic in `worker.py` for parallel, non-blocking LLM calls (2x-3x speedup).
- **Satisficer 2.0 (Judge)** ⚖️: Real-world QA loop in `judge.py` performing physical file checks and logical audits (non-hallucinated).
- **DTU-Lite** 👯: Digital Twin Universe -> Local mocks for Stripe, Auth, Discord, etc.

## 🚀 Usage

### 1. Define your Vibe
Edit `vibe.md` with your rough idea.

### 2. Run the Foreman
```bash
python foreman.py plan
```
*Generates `specs/specs.md` and `scenarios/scenarios.md`.*

### 3. Run the Factory (Parallel Build)
```bash
python worker.py build --specs specs/specs.md --output output_001
```
*Reads specs and generates code in `output/` via parallel specialists.*

### 4. Run the Satisficer (QA Audit)
```bash
python judge.py judge --scenarios scenarios/scenarios.md --output output_001
```
*Performs physical file checks and logical audits against the generated build.*

## 🛠️ Configuration

Configure your models in environment variables or `.env`.

**Foreman (The Brains):**
```bash
export FOREMAN_MODEL="claude-3-opus-20240229"
```

**Workers (The Labor):**
```bash
# Suggested: qwen2.5-coder:7b or deepseek-coder-v2:16b
export WORKER_BASE_URL="http://localhost:11434/v1"
export WORKER_MODEL="qwen2.5-coder:latest" 
```

---
> [!TIP]
> **Performance**: Use locally hosted Ollama for the Workers to eliminate rate limits and API costs during high-concurrency builds.
